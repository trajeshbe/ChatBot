"""
Email Sender

This module sends extraction results via email with file attachments.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class EmailSender:
    """Send files via email"""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True
    ):
        """
        Initialize email sender

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            use_tls: Whether to use TLS
        """
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.use_tls = use_tls

    async def deliver(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send file via email

        Args:
            file_path: Path to file to send
            config: Delivery configuration with keys:
                - to: Recipient email(s) (string or list)
                - subject: Email subject
                - body: Email body (optional)
                - cc: CC recipients (optional)
                - bcc: BCC recipients (optional)

        Returns:
            Delivery result
        """
        logger.info(f"Sending file via email: {file_path}")

        try:
            # Validate configuration
            recipients = config.get('to')
            if not recipients:
                raise ValueError("Email 'to' field is required")

            if isinstance(recipients, str):
                recipients = [recipients]

            subject = config.get('subject', 'Data Extraction Results')
            body = config.get('body', 'Please find attached data extraction results.')

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            # Add CC if provided
            if config.get('cc'):
                cc_list = config['cc'] if isinstance(config['cc'], list) else [config['cc']]
                msg['Cc'] = ', '.join(cc_list)
                recipients.extend(cc_list)

            # Add body
            msg.attach(MIMEText(body, 'plain'))

            # Attach file
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)

                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
            else:
                raise FileNotFoundError(f"File not found: {file_path}")

            # Send email
            if not self.smtp_user or not self.smtp_password:
                raise ValueError("SMTP credentials not configured")

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {len(recipients)} recipient(s)")

            return {
                'success': True,
                'method': 'email',
                'destination': ', '.join(recipients),
                'delivered_at': datetime.utcnow(),
                'error': None,
                'metadata': {
                    'recipients': recipients,
                    'subject': subject,
                    'file_name': os.path.basename(file_path)
                }
            }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'method': 'email',
                'destination': config.get('to', 'unknown'),
                'delivered_at': None,
                'error': str(e),
                'metadata': {}
            }


# Export
__all__ = ['EmailSender']
