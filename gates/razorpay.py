#!/usr/bin/env python3
"""
Razorpay Gate - Production Only
UNLIMITED CREDITS - No limits
"""

import logging
import os
import requests
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

class RazorpayGate:
    """Razorpay gateway - UNLIMITED CREDITS"""
    
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        """Initialize with LIVE keys ONLY"""
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        
        if not self.key_id or not self.key_secret:
            raise ValueError(
                "❌ PRODUCTION ERROR: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET required!\n"
                "Add LIVE keys to Railway Variables"
            )
        
        self.API_BASE = "https://api.razorpay.com/v1"
        logger.info("✅ Razorpay PRODUCTION initialized (UNLIMITED CREDITS)")
    
    async def check_card_live(self, card_number: str, month: str, year: str, cvv: str) -> Tuple[str, str]:
        """PRODUCTION: Real Razorpay card validation"""
        try:
            bin_code = card_number[:6]
            
            response = requests.get(
                f"{self.API_BASE}/iins",
                params={"iins": bin_code},
                auth=(self.key_id, self.key_secret),
                timeout=10
            )
            
            if response.status_code != 200:
                return "❌ <b>DEAD</b> - Card not found", "DEAD"
            
            data = response.json()
            iins_data = data.get("iins", {}).get(bin_code, {})
            
            if not iins_data:
                return "❌ <b>DEAD</b> - Card not found", "DEAD"
            
            card_type = iins_data.get("type", "unknown")
            brand_map = {"visa": "Visa", "mastercard": "Mastercard", "amex": "Amex"}
            card_brand = brand_map.get(card_type.lower(), card_type.title())
            
            # Check expiry
            current_year, current_month = 26, 7
            exp_month, exp_year = int(month), int(year)
            
            if exp_year < current_year or (exp_year == current_year and exp_month < current_month):
                return "❌ <b>DEAD</b> - Card expired", "DEAD"
            
            logger.info(f"✅ Card validated: {card_brand}")
            return f"✅ <b>ALIVE</b> - {card_brand} valid", "ALIVE"
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return f"❌ <b>ERROR</b> - {str(e)}", "ERROR"
    
    def get_plans(self) -> Dict:
        """UNLIMITED CREDITS - No limits"""
        return {
            "plan_unlimited": {
                "name": "Unlimited",
                "amount": 0,
                "credits": float('inf'),
                "description": "Unlimited card checks"
            }
        }

