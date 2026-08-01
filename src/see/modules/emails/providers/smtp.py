"""SMTP verification provider for email OSINT."""

from __future__ import annotations

import asyncio
import smtplib
import socket
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import DisposableResult
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("smtp_provider")


class SMTPProvider(BaseEmailProvider):
    """
    Provider for SMTP email verification.
    
    Checks if an email address exists by connecting to the SMTP server
    and verifying the recipient without sending any email.
    No API key required.
    """
    
    @property
    def name(self) -> str:
        return "smtp"
    
    @property
    def description(self) -> str:
        return "SMTP email verification - check if email exists"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    @property
    def supports_disposable(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True
    
    async def check_disposable(self, email: str, config: AppConfig) -> DisposableResult | None:
        """Check if email is deliverable via SMTP."""
        logger.info(f"Running SMTP verification for {email}")
        
        domain = email.split('@')[-1].lower() if '@' in email else ''
        
        if not domain:
            return None
        
        try:
            # Get MX records
            mx_records = await self._get_mx_records(domain)
            
            if not mx_records:
                return DisposableResult(
                    source="smtp",
                    email=email,
                    is_disposable=False,
                    is_webmail=False,
                    provider=domain.split('.')[0],
                    mx_found=False,
                )
            
            # Try to connect to SMTP server and verify email
            is_deliverable = await self._verify_email(email, mx_records[0])
            
            return DisposableResult(
                source="smtp",
                email=email,
                is_disposable=False,
                is_webmail=False,
                provider=domain.split('.')[0],
                mx_found=True,
            )
            
        except Exception as e:
            logger.error(f"SMTP verification failed: {e}")
            return None
    
    async def _get_mx_records(self, domain: str) -> list[str]:
        """Get MX records for domain."""
        try:
            import dns.resolver
            
            def resolve_mx():
                mx_records = []
                answers = dns.resolver.resolve(domain, 'MX')
                for rdata in sorted(answers, key=lambda x: x.preference):
                    mx_records.append(str(rdata.exchange).rstrip('.'))
                return mx_records
            
            return await asyncio.to_thread(resolve_mx)
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")
            return []
    
    async def _verify_email(self, email: str, mx_host: str) -> bool:
        """Verify email by connecting to SMTP server."""
        try:
            # Run SMTP verification in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._smtp_check,
                email,
                mx_host,
            )
            return result
        except Exception as e:
            logger.error(f"SMTP check failed: {e}")
            return False
    
    def _smtp_check(self, email: str, mx_host: str) -> bool:
        """Perform SMTP check (sync)."""
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_host, 25)
            server.helo('check-email-verify.com')
            server.mail('check@check-email-verify.com')
            
            # Check if recipient exists
            code, message = server.rcpt(email)
            
            server.quit()
            
            # Code 250 means recipient exists
            return code == 250
            
        except smtplib.SMTPServerDisconnected:
            logger.debug(f"SMTP server disconnected for {mx_host}")
            return False
        except smtplib.SMTPConnectError:
            logger.debug(f"SMTP connection failed for {mx_host}")
            return False
        except socket.timeout:
            logger.debug(f"SMTP timeout for {mx_host}")
            return False
        except Exception as e:
            logger.debug(f"SMTP check error: {e}")
            return False
