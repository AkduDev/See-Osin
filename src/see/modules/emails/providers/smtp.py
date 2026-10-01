"""SMTP verification provider for email OSINT."""

from __future__ import annotations

import asyncio
import smtplib
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("smtp_provider")


class SMTPProvider(BaseEmailProvider):
    """
    Provider for SMTP email verification.

    Checks if an email address is deliverable by connecting to the
    domain's MX server and issuing RCPT TO without sending any mail.
    No API key required.

    Note: many providers (Gmail, Outlook, ...) accept-all or greylist,
    so a negative result is conclusive but a positive one is not proof
    that the mailbox exists.
    """

    @property
    def name(self) -> str:
        return "smtp"

    @property
    def description(self) -> str:
        return "SMTP email verification - check if email is deliverable"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def supports_verification(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True

    async def verify_deliverability(
        self, email: str, config: AppConfig
    ) -> dict[str, Any] | None:
        """Verify whether an email address looks deliverable via SMTP."""
        logger.info(f"Running SMTP verification for {email}")

        domain = email.split("@")[-1].lower() if "@" in email else ""

        if not domain:
            return None

        try:
            mx_records = await self._get_mx_records(domain)

            if not mx_records:
                return {
                    "email": email,
                    "domain": domain,
                    "mx_found": False,
                    "mx_host": "",
                    "is_deliverable": False,
                    "smtp_code": None,
                }

            code = await self._verify_email(email, mx_records[0])

            return {
                "email": email,
                "domain": domain,
                "mx_found": True,
                "mx_host": mx_records[0],
                "is_deliverable": code == 250,
                "smtp_code": code,
            }

        except Exception as e:
            logger.error(f"SMTP verification failed: {e}")
            return None

    async def _get_mx_records(self, domain: str) -> list[str]:
        """Get MX records for domain."""
        try:
            import dns.resolver

            def resolve_mx():
                mx_records = []
                answers = dns.resolver.resolve(domain, "MX")
                for rdata in sorted(answers, key=lambda x: x.preference):
                    mx_records.append(str(rdata.exchange).rstrip("."))
                return mx_records

            return await asyncio.to_thread(resolve_mx)
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")
            return []

    async def _verify_email(self, email: str, mx_host: str) -> int | None:
        """Verify email by connecting to SMTP server. Returns SMTP code."""
        try:
            return await asyncio.to_thread(self._smtp_check, email, mx_host)
        except Exception as e:
            logger.error(f"SMTP check failed: {e}")
            return None

    def _smtp_check(self, email: str, mx_host: str) -> int | None:
        """Perform SMTP check (sync). Returns RCPT TO response code."""
        try:
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_host, 25)
            server.helo("check-email-verify.com")
            server.mail("check@check-email-verify.com")

            code, _message = server.rcpt(email)

            try:
                server.quit()
            except Exception as e:
                logger.debug(f"SMTP quit failed: {e}")

            return int(code)

        except smtplib.SMTPServerDisconnected:
            logger.debug(f"SMTP server disconnected for {mx_host}")
            return None
        except smtplib.SMTPConnectError:
            logger.debug(f"SMTP connection failed for {mx_host}")
            return None
        except TimeoutError:
            logger.debug(f"SMTP timeout for {mx_host}")
            return None
        except Exception as e:
            logger.debug(f"SMTP check error: {e}")
            return None
