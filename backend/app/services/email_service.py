import os
import smtplib
import logging
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
        Uses configured SMTP or saves locally to backend/reports/ with clear delivery logs.
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

        # Check if live SMTP is configured
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
                msg["To"] = to_email
                msg["Subject"] = subject

                body_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6;">
                    <div style="background-color: #0f172a; color: white; padding: 20px; border-radius: 8px;">
                        <h2 style="margin: 0; color: #38bdf8;">AI Voice Interview Assessment</h2>
                        <p style="margin: 5px 0 0 0; color: #94a3b8;">Candidate Technical Evaluation Report</p>
                    </div>
                    <div style="padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 15px;">
                        <p>Hello HR Team,</p>
                        <p>Candidate <strong>{candidate_name}</strong> has just completed their AI Voice Interview.</p>
                        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Overall Score:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; color: #0284c7; font-weight: bold;">{overall_score}/100</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Recommendation:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{recommendation}</td>
                            </tr>
                        </table>
                        <p>The complete official PDF report is attached to this email.</p>
                        <br/>
                        <p style="font-size: 12px; color: #64748b;">Generated automatically by AI Voice Interviewer.</p>
                    </div>
                </body>
                </html>
                """
                msg.attach(MIMEText(body_html, "html"))

                # Attach PDF
                attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
                attachment.add_header("Content-Disposition", "attachment", filename=f"{safe_name}_interview_report.pdf")
                msg.attach(attachment)

                # Connect & send
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                logger.info(f"Successfully emailed interview report PDF to {to_email}")
                return {
                    "status": "sent",
                    "recipient": to_email,
                    "method": "smtp",
                    "pdf_file": local_filename
                }
            except Exception as e:
                logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
                return {
                    "status": "smtp_failed_saved_locally",
                    "recipient": to_email,
                    "error": str(e),
                    "pdf_file": local_filename,
                    "pdf_path": local_path
                }
        else:
            logger.info(f"SMTP not configured. Report PDF archived locally for HR at {local_path} (Target: {to_email})")
            return {
                "status": "archived_for_hr",
                "recipient": to_email,
                "note": f"PDF generated for {to_email} and saved to {local_path}. To send live emails to your inbox, configure SMTP in backend/.env.",
                "pdf_file": local_filename,
                "pdf_path": local_path
            }
