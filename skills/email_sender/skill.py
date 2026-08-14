"""
EvolvixOS — Email Sender Skill
Send emails via SMTP. All local, no API needed.
100% local using smtplib. Zero tokens.

No pip install needed (stdlib smtplib).
License: PSF (Python stdlib)
"""

import os
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Email sender — send via any SMTP server. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/emails"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, args: dict) -> str:
        action = args.get("action", "send")

        if action == "send":
            return self.send(
                args.get("to", ""), args.get("subject", ""),
                args.get("body", ""), args.get("html", False),
                args.get("attachments", []),
            )
        elif action == "send_bulk":
            return self.send_bulk(
                args.get("recipients", []), args.get("subject", ""),
                args.get("body", ""),
            )
        elif action == "send_template":
            return self.send_template(
                args.get("to", ""), args.get("template", ""),
                args.get("variables", {}),
            )
        else:
            return f"Unknown action: {action}. Use: send, send_bulk, send_template"

    def send(self, to: str, subject: str, body: str, html: bool = False,
             attachments: list = None) -> str:
        if not to or not subject:
            return "Error: 'to' and 'subject' are required."

        smtp_host = os.environ.get("SMTP_HOST", self.config.get("smtp_host", "localhost"))
        smtp_port = int(os.environ.get("SMTP_PORT", self.config.get("smtp_port", 25)))
        smtp_user = os.environ.get("SMTP_USER", self.config.get("smtp_user", ""))
        smtp_pass = os.environ.get("SMTP_PASS", self.config.get("smtp_pass", ""))
        from_addr = os.environ.get("SMTP_FROM", self.config.get("from_addr", smtp_user or "evolvix@localhost"))

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html" if html else "plain"))

        # Attachments
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    part = MIMEBase("application", "octet-stream")
                    with open(filepath, "rb") as f:
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition",
                                    f"attachment; filename={Path(filepath).name}")
                    msg.attach(part)

        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                if smtp_port == 587:
                    server.starttls()

            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)

            server.sendmail(from_addr, to.split(","), msg.as_string())
            server.quit()

            # Log
            log = self.output_dir / f"sent_{int(time.time())}.json"
            log.write_text(json.dumps({
                "to": to, "subject": subject,
                "timestamp": time.time(), "status": "sent",
            }, indent=2))

            return f"Email sent to {to}: {subject}"
        except Exception as e:
            return f"Error sending email: {e}"

    def send_bulk(self, recipients: List[str], subject: str, body: str) -> str:
        results = []
        for r in recipients:
            result = self.send(r, subject, body)
            results.append({"to": r, "result": result})
        sent = sum(1 for r in results if "sent" in r["result"])
        return f"Sent {sent}/{len(recipients)} emails"

    def send_template(self, to: str, template: str, variables: dict) -> str:
        """Send email using a template with variable substitution."""
        body = template
        for key, value in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(value))
        return self.send(to, f"Message from EvolvixOS", body)
