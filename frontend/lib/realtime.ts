/**
 * Client-side OpenAI Realtime WebRTC integration.
 * Securely uses the ephemeral client_secret obtained from FastAPI backend.
 * Never requires or exposes the permanent OpenAI API key.
 */

export interface RealtimeCallbacks {
  onStatusChange?: (status: "connecting" | "speaking" | "listening" | "thinking" | "idle" | "error") => void;
  onAiTranscriptDelta?: (delta: string) => void;
  onAiTranscriptComplete?: (text: string) => void;
  onUserTranscriptComplete?: (text: string) => void;
  onError?: (err: Error) => void;
}

export class RealtimeVoiceSession {
  private pc: RTCPeerConnection | null = null;
  private dc: RTCDataChannel | null = null;
  private localStream: MediaStream | null = null;
  private audioEl: HTMLAudioElement | null = null;
  private callbacks: RealtimeCallbacks;
  private isConnected = false;

  constructor(callbacks: RealtimeCallbacks = {}) {
    this.callbacks = callbacks;
  }

  public async start(clientSecret: string, model: string = "gpt-4o-realtime-preview-2024-12-17"): Promise<void> {
    try {
      this.callbacks.onStatusChange?.("connecting");

      // 1. Request microphone access
      this.localStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // 2. Initialize RTCPeerConnection
      this.pc = new RTCPeerConnection();

      // 3. Setup remote audio player
      this.audioEl = document.createElement("audio");
      this.audioEl.autoplay = true;
      this.pc.ontrack = (event) => {
        if (this.audioEl) {
          this.audioEl.srcObject = event.streams[0];
          this.audioEl.play().catch((err) => console.warn("Audio autoplay blocked:", err));
        }
      };

      // 4. Add local audio tracks to peer connection
      for (const track of this.localStream.getTracks()) {
        this.pc.addTrack(track, this.localStream);
      }

      // 5. Establish RTC DataChannel for Realtime events
      this.dc = this.pc.createDataChannel("oai-events");
      this.setupDataChannel(this.dc);

      // 6. Create SDP Offer
      const offer = await this.pc.createOffer();
      await this.pc.setLocalDescription(offer);

      // 7. Connect to OpenAI Realtime WebRTC gateway using ephemeral client_secret
      const baseUrl = "https://api.openai.com/v1/realtime";
      const sdpResponse = await fetch(`${baseUrl}?model=${encodeURIComponent(model)}`, {
        method: "POST",
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${clientSecret}`,
          "Content-Type": "application/sdp",
        },
      });

      if (!sdpResponse.ok) {
        const errorText = await sdpResponse.text();
        throw new Error(`OpenAI Realtime WebRTC handshake failed: ${sdpResponse.status} - ${errorText}`);
      }

      const answerSdp = await sdpResponse.text();
      await this.pc.setRemoteDescription({
        type: "answer",
        sdp: answerSdp,
      });

      this.isConnected = true;
      this.callbacks.onStatusChange?.("listening");
    } catch (error: any) {
      console.error("Realtime session start error:", error);
      this.callbacks.onStatusChange?.("error");
      this.callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
      this.stop();
      throw error;
    }
  }

  private setupDataChannel(channel: RTCDataChannel) {
    channel.onopen = () => {
      console.log("Realtime DataChannel opened");
    };

    channel.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.handleServerEvent(msg);
      } catch (err) {
        console.warn("Failed to parse realtime event JSON:", event.data);
      }
    };

    channel.onerror = (err) => {
      console.error("Realtime DataChannel error:", err);
    };
  }

  private handleServerEvent(event: any) {
    switch (event.type) {
      // AI Spoken Audio transcript stream
      case "response.audio_transcript.delta":
        if (event.delta) {
          this.callbacks.onStatusChange?.("speaking");
          this.callbacks.onAiTranscriptDelta?.(event.delta);
        }
        break;

      case "response.audio_transcript.done":
        if (event.transcript) {
          this.callbacks.onAiTranscriptComplete?.(event.transcript);
        }
        break;

      case "response.created":
        this.callbacks.onStatusChange?.("thinking");
        break;

      case "response.done":
        this.callbacks.onStatusChange?.("listening");
        break;

      // Candidate microphone transcription completed by server Whisper
      case "conversation.item.input_audio_transcription.completed":
        if (event.transcript) {
          this.callbacks.onUserTranscriptComplete?.(event.transcript.trim());
        }
        break;

      case "input_audio_buffer.speech_started":
        this.callbacks.onStatusChange?.("listening");
        break;

      case "input_audio_buffer.speech_stopped":
        this.callbacks.onStatusChange?.("thinking");
        break;

      case "error":
        console.error("OpenAI Realtime server error event:", event.error);
        break;

      default:
        break;
    }
  }

  public sendTextMessage(text: string) {
    if (!this.dc || this.dc.readyState !== "open") {
      console.warn("Cannot send message: DataChannel is not open");
      return;
    }

    const event = {
      type: "conversation.item.create",
      item: {
        type: "message",
        role: "user",
        content: [{ type: "input_text", text }],
      },
    };

    this.dc.send(JSON.stringify(event));
    this.dc.send(JSON.stringify({ type: "response.create" }));
  }

  public stop(): void {
    if (this.dc) {
      try {
        this.dc.close();
      } catch {}
      this.dc = null;
    }

    if (this.pc) {
      try {
        this.pc.close();
      } catch {}
      this.pc = null;
    }

    if (this.localStream) {
      for (const track of this.localStream.getTracks()) {
        track.stop();
      }
      this.localStream = null;
    }

    if (this.audioEl) {
      this.audioEl.srcObject = null;
      this.audioEl.remove();
      this.audioEl = null;
    }

    this.isConnected = false;
    this.callbacks.onStatusChange?.("idle");
  }

  public get active(): boolean {
    return this.isConnected;
  }
}

