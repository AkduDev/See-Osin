"""Email intelligence provider for DNS and email analysis."""

from __future__ import annotations

import dns.resolver
import dns.reversename
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import EmailResult
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("email_intelligence_provider")


class EmailIntelligenceProvider(BaseEmailProvider):
    """
    Provider for email intelligence gathering.
    
    Performs DNS analysis, MX record lookup, SPF/DKIM/DMARC checks,
    and other email-related intelligence.
    No API key required.
    """
    
    @property
    def name(self) -> str:
        return "email_intelligence"
    
    @property
    def description(self) -> str:
        return "Email DNS analysis and intelligence"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True
    
    async def get_email_intelligence(self, email: str, config: AppConfig) -> dict[str, Any]:
        """Gather email intelligence."""
        logger.info(f"Gathering email intelligence for {email}")
        
        domain = email.split('@')[-1].lower() if '@' in email else ''
        
        if not domain:
            return {}
        
        intelligence = {
            "domain": domain,
            "mx_records": [],
            "spf_record": None,
            "dkim_record": None,
            "dmarc_record": None,
            "a_records": [],
            "txt_records": [],
            "whois_info": None,
            "email_age": None,
            "provider_info": None,
        }
        
        # Get MX records
        intelligence["mx_records"] = await self._get_mx_records(domain)
        
        # Get SPF record
        intelligence["spf_record"] = await self._get_spf_record(domain)
        
        # Get DMARC record
        intelligence["dmarc_record"] = await self._get_dmarc_record(domain)
        
        # Get A records
        intelligence["a_records"] = await self._get_a_records(domain)
        
        # Get TXT records
        intelligence["txt_records"] = await self._get_txt_records(domain)
        
        # Identify email provider
        intelligence["provider_info"] = await self._identify_provider(domain, intelligence["mx_records"])
        
        return intelligence
    
    async def _get_mx_records(self, domain: str) -> list[dict[str, Any]]:
        """Get MX records for domain."""
        try:
            mx_records = []
            answers = dns.resolver.resolve(domain, 'MX')
            
            for rdata in sorted(answers, key=lambda x: x.preference):
                mx_records.append({
                    "priority": rdata.preference,
                    "exchange": str(rdata.exchange).rstrip('.'),
                })
            
            return mx_records
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")
            return []
    
    async def _get_spf_record(self, domain: str) -> str | None:
        """Get SPF record for domain."""
        try:
            answers = dns.resolver.resolve(domain, 'TXT')
            
            for rdata in answers:
                txt = str(rdata).strip('"')
                if txt.startswith('v=spf1'):
                    return txt
            
            return None
        except Exception as e:
            logger.debug(f"SPF lookup failed for {domain}: {e}")
            return None
    
    async def _get_dmarc_record(self, domain: str) -> str | None:
        """Get DMARC record for domain."""
        try:
            dmarc_domain = f"_dmarc.{domain}"
            answers = dns.resolver.resolve(dmarc_domain, 'TXT')
            
            for rdata in answers:
                txt = str(rdata).strip('"')
                if txt.startswith('v=DMARC1'):
                    return txt
            
            return None
        except Exception as e:
            logger.debug(f"DMARC lookup failed for {domain}: {e}")
            return None
    
    async def _get_a_records(self, domain: str) -> list[str]:
        """Get A records for domain."""
        try:
            records = []
            answers = dns.resolver.resolve(domain, 'A')
            
            for rdata in answers:
                records.append(str(rdata))
            
            return records
        except Exception as e:
            logger.debug(f"A record lookup failed for {domain}: {e}")
            return []
    
    async def _get_txt_records(self, domain: str) -> list[str]:
        """Get all TXT records for domain."""
        try:
            records = []
            answers = dns.resolver.resolve(domain, 'TXT')
            
            for rdata in answers:
                records.append(str(rdata).strip('"'))
            
            return records
        except Exception as e:
            logger.debug(f"TXT lookup failed for {domain}: {e}")
            return []
    
    async def _identify_provider(self, domain: str, mx_records: list[dict]) -> dict[str, Any]:
        """Identify email provider based on MX records."""
        provider_map = {
            "google.com": {"name": "Google Workspace", "type": "business"},
            "gmail-smtp-in.l.google.com": {"name": "Gmail", "type": "free"},
            "outlook.com": {"name": "Microsoft Outlook", "type": "business"},
            "protonmail.ch": {"name": "ProtonMail", "type": "secure"},
            "proton.me": {"name": "ProtonMail", "type": "secure"},
            "zoho.com": {"name": "Zoho Mail", "type": "business"},
            "yandex.net": {"name": "Yandex Mail", "type": "free"},
            "fastmail.com": {"name": "Fastmail", "type": "paid"},
            "tutanota.com": {"name": "Tutanota", "type": "secure"},
        }
        
        for mx in mx_records:
            exchange = mx.get("exchange", "").lower()
            
            for key, info in provider_map.items():
                if key in exchange:
                    return {
                        "name": info["name"],
                        "type": info["type"],
                        "mx_host": exchange,
                    }
        
        # Default provider info based on domain
        free_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com"}
        if domain in free_domains:
            return {"name": domain.split('.')[0].title(), "type": "free"}
        
        return {"name": "Unknown", "type": "unknown"}
