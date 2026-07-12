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
        ALWAYS returns real BIN info (never default)
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
                # TRY AGAIN if first attempt fails
                # Don't return default, retry once more
                try:
                    response = requests.get(
                        url,
                        auth=(self.key_id, self.key_secret),
                        timeout=3
                    )
                    if response.status_code == 200:
                        data = response.json()
                        iin_data = data.get("iin", {})
                        bin_info = {
                            "brand": iin_data.get("network", "UNKNOWN").upper(),
                            "type": iin_data.get("type", "UNKNOWN").upper(),
                            "level": iin_data.get("sub_type", "CLASSIC").upper(),
                            "bank": iin_data.get("issuer_name", "UNKNOWN"),
                            "country": iin_data.get("issuer_country", "UNKNOWN"),
                        }
                        self.bin_cache[bin_code] = bin_info
                        return bin_info
                except:
                    pass
                
                # If API fails completely, return unknown but NOT default Sutton
                return {
                    "brand": "UNKNOWN",
                    "type": "UNKNOWN",
                    "level": "UNKNOWN",
                    "bank": "UNKNOWN",
                    "country": "UNKNOWN"
                }
        
        except Exception as e:
            logger.error(f"✗ BIN fetch failed: {str(e)}")
            # Return UNKNOWN, NOT default
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
        ALWAYS fetch real BIN info regardless of status
        
        Returns:
            (card_info_dict, status) where status = "ALIVE" or "DECLINED"
        """
        
        try:
            # Get BIN code
            bin_code = card_num[:6]
            
            # ALWAYS fetch real BIN info (from cache or API)
            # This ensures DECLINED cards show their real BIN, not default
            bin_info = await self.get_bin_info(bin_code)
            
            # Validate card with Razorpay
            # The card validation will determine ALIVE/DECLINED
            payload = {
                "card_number": card_num,
                "cvv": cvv,
                "expiry_month": month,
                "expiry_year": f"20{year}",  # Convert YY to YYYY
            }
            
            url = f"{self.base_url}/cards/validation"
            
            status = "DECLINED"  # Default to DECLINED
            
            try:
                response = requests.post(
                    url,
                    json=payload,
                    auth=(self.key_id, self.key_secret),
                    timeout=5
                )
                
                # ALIVE if response is 200
                if response.status_code == 200:
                    status = "ALIVE"
            
            except Exception as e:
                logger.warning(f"Card validation API error: {str(e)}")
                # On API error, assume DECLINED
                status = "DECLINED"
            
            # Build response dict with REAL BIN info
            # This is used for BOTH ALIVE and DECLINED cards
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
            
            logger.info(f"Card {card_num[-4:]} - {status} - BIN: {bin_code}")
            
            return card_info, status
        
        except Exception as e:
            logger.error(f"Card check failed: {str(e)}")
            # Return with UNKNOWN bin_info (not default)
            return {
                "card": "UNKNOWN",
                "gateway": "RazorPay",
                "response": "Error",
                "brand": "UNKNOWN",
                "type": "UNKNOWN",
                "level": "UNKNOWN",
                "bank": "UNKNOWN",
                "country": "UNKNOWN"
            }, "ERROR"

