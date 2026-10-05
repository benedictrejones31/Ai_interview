import os
import smtplib
import logging
import base64
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_interview_report(
        candidate_name: str,
        overall_score: int,
        recommendation: str,
        pdf_bytes: bytes,
        recipient_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send the official PDF interview report to HR (default: benedictrejones3101@gmail.com).
        Prioritizes Resend API, falls back to SMTP or local reports archive.
        """
        to_email = recipient_email or settings.HR_NOTIFICATION_EMAIL or "benedictrejones3101@gmail.com"
        subject = f"Interview Assessment Completed: {candidate_name} - Score: {overall_score}/100"
        
        # Save a copy locally regardless
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '_', '-')).strip()
        local_filename = f"report_{safe_name.replace(' ', '_')}_{overall_score}.pdf"
        local_path = os.path.join(reports_dir, local_filename)
        with open(local_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Report PDF archived locally at {local_path}")

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6; margin: 0; padding: 20px; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
                <div style="background-color: #0f172a; color: white; padding: 24px; text-align: left;">
                    <h2 style="margin: 0; color: #38bdf8; font-size: 20px;">AI Voice Interviewer</h2>
                    <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 13px;">Candidate Technical Assessment Report</p>
                </div>
                <div style="padding: 24px;">
                    <p style="font-size: 15px; margin-top: 0;">Hello HR Team,</p>
                    <p style="font-size: 14px; color: #334155;">Candidate <strong>{candidate_name}</strong> has completed their AI voice interview. The technical assessment breakdown is provided below:</p>
                    
                    <div style="background-color: #f1f5f9; border-radius: 8px; padding: 16px; margin: 20px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #475569; font-size: 13px;"><strong>Overall Score:</strong></td>
                                <td style="padding: 8px 0; color: #0284c7; font-weight: bold; font-size: 18px; text-align: right;">{overall_score}/100</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #475569; font-size: 13px;"><strong>Recommendation:</strong></td>
                                <td style="padding: 8px 0; color: #0f172a; font-weight: 600; font-size: 13px; text-align: right;">{recommendation}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="font-size: 13px; color: #334155;">The official synthesized PDF report is attached to this email with all competency pillars, strengths, and question analyses.</p>
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
                    <p style="font-size: 11px; color: #94a3b8; margin: 0;">Automated assessment report sent via Resend by AI Voice Interviewer.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 1. Primary Service: Resend API (https://resend.com)
        if settings.RESEND_API_KEY:
            try:
                encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                resend_url = "https://api.resend.com/emails"
                resend_headers = {
                    "Authorization": f"Bearer {settings.RESEND_API_KEY.strip()}",
                    "Content-Type": "application/json"
                }
                resend_payload = {
                    "from": settings.RESEND_FROM or "AI Voice Interviewer <onboarding@resend.dev>",
                    "to": [to_email],
                    "subject": subject,
                    "html": body_html,
                    "attachments": [
                        {
                            "filename": f"{safe_name}_interview_report.pdf",
                            "content": encoded_pdf
                        }
                    ]
                }
                with httpx.Client(timeout=20.0) as client:
                    resp = client.post(resend_url, headers=resend_headers, json=resend_payload)

                if resp.status_code in (200, 201):
                    res_json = resp.json()
                    resend_id = res_json.get("id")
                    logger.info(f"Successfully emailed interview report via Resend to {to_email} (ID: {resend_id})")
                    return {
                        "status": "sent",
                        "recipient": to_email,
                        "method": "resend",
                        "resend_id": resend_id,
                        "pdf_file": local_filename,
                        "pdf_path": local_path
                    }
                else:
                    logger.warning(f"Resend API returned status {resp.status_code}: {resp.text}. Trying fallback.")
            except Exception as resend_err:
                logger.error(f"Failed to dispatch email via Resend to {to_email}: {resend_err}")

        # 2. Secondary Fallback: Standard SMTP
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
                msg["To"] = to_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body_html, "html"))

                attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
                attachment.add_header("Content-Disposition", "attachment", filename=f"{safe_name}_interview_report.pdf")
                msg.attach(attachment)

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                logger.info(f"Successfully emailed interview report PDF via SMTP to {to_email}")
                return {
                    "status": "sent",
                    "recipient": to_email,
                    "method": "smtp",
                    "pdf_file": local_filename,
                    "pdf_path": local_path
                }
            except Exception as smtp_err:
                logger.error(f"Failed to send email via SMTP to {to_email}: {smtp_err}")

        # 3. Local Archive Fallback
        logger.info(f"Report PDF archived locally for HR at {local_path} (Target: {to_email})")
        return {
            "status": "archived_for_hr",
            "recipient": to_email,
            "note": f"PDF generated for {to_email} and saved to {local_path}.",
            "pdf_file": local_filename,
            "pdf_path": local_path
        }
