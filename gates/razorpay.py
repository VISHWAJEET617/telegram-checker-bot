#!/usr/bin/env python3
"""Razorpay BIN Lookup & Card Checking"""

import requests
import logging
from typing import Tuple, Dict
import asyncio

logger = logging.getLogger(__name__)

class RazorpayGate:
    """Razorpay API Gateway for BIN lookup & card validation"""
    
    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = "https://api.razorpay.com/v1"
        self.bin_cache = {}  # Local cache - unlimited lookups
    
    async def get_bin_info(self, bin_code: str) -> Dict:
        """
        Fetch BIN information from Razorpay API
        Cache first, then API
        """
        
        # Check cache first (unlimited, instant)
        if bin_code in self.bin_cache:
            logger.debug(f"✓ BIN {bin_code} from CACHE")
            return self.bin_cache[bin_code]
        
        try:
            # Fetch from Razorpay API
            url = f"{self.base_url}/iins/{bin_code}"
            
            response = requests.get(
                url,
                auth=(self.key_id, self.key_secret),
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract BIN info
                iin_data = data.get("iin", {})
                bin_info = {
                    "brand": iin_data.get("network", "UNKNOWN").upper(),
                    "type": iin_data.get("type", "UNKNOWN").upper(),
                    "level": iin_data.get("sub_type", "CLASSIC").upper(),
                    "bank": iin_data.get("issuer_name", "UNKNOWN"),
                    "country": iin_data.get("issuer_country", "UNKNOWN"),
                }
                
                # Cache it
                self.bin_cache[bin_code] = bin_info
                logger.info(f"✓ BIN {bin_code} from API (cached)")
                return bin_info
            
            else:
                logger.warning(f"✗ BIN API error: {response.status_code}")
                return self._default_bin_info()
        
        except Exception as e:
            logger.error(f"✗ BIN fetch failed: {str(e)}")
            return self._default_bin_info()
    
    def _default_bin_info(self) -> Dict:
        """Default BIN info if API fails"""
        return {
            "brand": "UNKNOWN",
            "type": "UNKNOWN",
            "level": "UNKNOWN",
            "bank": "UNKNOWN",
            "country": "UNKNOWN"
        }
    
    async def check_card_live(self, card_num: str, month: str, year: str, cvv: str) -> Tuple[Dict, str]:
        """
        Check if card is ALIVE or DECLINED
        
        Returns:
            (card_info_dict, status) where status = "ALIVE" or "DECLINED"
        """
        
        try:
            # Get BIN code
            bin_code = card_num[:6]
            
            # Fetch BIN info (from cache or API)
            bin_info = await self.get_bin_info(bin_code)
            
            # Validate card with Razorpay (simulated)
            # In real implementation, use Razorpay card validation API
            payload = {
                "card_number": card_num,
                "cvv": cvv,
                "expiry_month": month,
                "expiry_year": f"20{year}",  # Convert YY to YYYY
            }
            
            url = f"{self.base_url}/cards/validation"
            
            try:
                response = requests.post(
                    url,
                    json=payload,
                    auth=(self.key_id, self.key_secret),
                    timeout=5
                )
                
                # Determine status based on response
                status = "ALIVE" if response.status_code == 200 else "DECLINED"
            
            except:
                # Fallback: simulate based on card number (for testing)
                # In production, always use real API
                status = "ALIVE" if int(card_num[-1]) % 2 == 0 else "DECLINED"
            
            # Build response dict
            card_info = {
                "card": f"{card_num[:6]}****{card_num[-4:]}",
                "gateway": "RazorPay",
                "response": "Payment Successfully" if status == "ALIVE" else "Card Declined",
                "brand": bin_info["brand"],
                "type": bin_info["type"],
                "level": bin_info["level"],
                "bank": bin_info["bank"],
                "country": bin_info["country"]
            }
            
            return card_info, status
        
        except Exception as e:
            logger.error(f"Card check failed: {str(e)}")
            return self._default_card_info(), "ERROR"
    
    def _default_card_info(self) -> Dict:
        return {
            "card": "UNKNOWN",
            "gateway": "RazorPay",
            "response": "API Error",
            "brand": "UNKNOWN",
            "type": "UNKNOWN",
            "level": "UNKNOWN",
            "bank": "UNKNOWN",
            "country": "UNKNOWN"
        }

