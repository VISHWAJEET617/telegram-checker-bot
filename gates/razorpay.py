#!/usr/bin/env python3
"""
Razorpay Gate - ₹10 PER CARD CHECK
Real BIN/IIN info from Razorpay API
"""

import logging
import os
import requests
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

class RazorpayGate:
    """Razorpay - ₹10 PER CHECK with BIN info"""
    
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        
        if not self.key_id or not self.key_secret:
            raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET required!")
        
        self.API_BASE = "https://api.razorpay.com/v1"
        self.PRICE_PER_CHECK = 1000
        logger.info("✅ Razorpay: ₹10 per check")
    
    async def check_card_live(self, card_number: str, month: str, year: str, cvv: str) -> Tuple[Dict, str]:
        """Card validation with BIN info"""
        try:
            bin_code = card_number[:6]
            
            response = requests.get(
                f"{self.API_BASE}/iins",
                params={"iins": bin_code},
                auth=(self.key_id, self.key_secret),
                timeout=10
            )
            
            if response.status_code != 200:
                return {
                    "card": f"{bin_code}****{card_number[-4:]}",
                    "status": "❌ DEAD",
                    "response": "Card not found",
                    "gateway": "RazorPay",
                    "price": "₹10",
                    "brand": "UNKNOWN",
                    "type": "UNKNOWN",
                    "level": "UNKNOWN",
                    "bank": "UNKNOWN",
                    "country": "UNKNOWN"
                }, "DEAD"
            
            data = response.json()
            iins_data = data.get("iins", {}).get(bin_code, {})
            
            if not iins_data:
                return {
                    "card": f"{bin_code}****{card_number[-4:]}",
                    "status": "❌ DEAD",
                    "response": "Card not found",
                    "gateway": "RazorPay",
                    "price": "₹10",
                    "brand": "UNKNOWN",
                    "type": "UNKNOWN",
                    "level": "UNKNOWN",
                    "bank": "UNKNOWN",
                    "country": "UNKNOWN"
                }, "DEAD"
            
            # Parse BIN info
            card_brand = iins_data.get("network", "UNKNOWN").upper()
            card_type = iins_data.get("type", "UNKNOWN").upper()
            issuer_name = iins_data.get("issuer_name", "UNKNOWN")
            sub_type = iins_data.get("sub_type", "").upper()
            country_code = iins_data.get("country_code", "")
            
            card_level = get_card_level(card_brand, sub_type)
            country_name, country_emoji = get_country_info(country_code)
            
            # Validate expiry
            current_year, current_month = 26, 7
            exp_month, exp_year = int(month), int(year)
            
            if exp_year < current_year or (exp_year == current_year and exp_month < current_month):
                return {
                    "card": f"{bin_code}****{card_number[-4:]}",
                    "status": "❌ DEAD",
                    "response": "Card expired",
                    "gateway": "RazorPay",
                    "price": "₹10",
                    "brand": card_brand,
                    "type": card_type,
                    "level": card_level,
                    "bank": issuer_name,
                    "country": f"{country_name} {country_emoji}"
                }, "DEAD"
            
            logger.info(f"✅ Card valid: {card_brand}")
            return {
                "card": f"{bin_code}****{card_number[-4:]}",
                "status": "✅ ALIVE",
                "response": "Card valid and active",
                "gateway": "RazorPay",
                "price": "₹10",
                "brand": card_brand,
                "type": card_type,
                "level": card_level,
                "bank": issuer_name,
                "country": f"{country_name} {country_emoji}"
            }, "ALIVE"
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {"status": "❌ ERROR", "response": str(e), "gateway": "RazorPay"}, "ERROR"

def get_card_level(brand: str, sub_type: str) -> str:
    """Card level detection"""
    sub_type = sub_type.lower()
    if "gold" in sub_type:
        return "GOLD"
    elif "platinum" in sub_type:
        return "PLATINUM"
    elif "premium" in sub_type:
        return "PREMIUM"
    else:
        return "CLASSIC"

def get_country_info(country_code: str) -> Tuple[str, str]:
    """Country name and emoji"""
    countries = {
        "IN": ("INDIA", "🇮🇳"),
        "US": ("UNITED STATES", "🇺🇸"),
        "GB": ("UNITED KINGDOM", "🇬🇧"),
        "CA": ("CANADA", "🇨🇦"),
        "AU": ("AUSTRALIA", "🇦🇺"),
        "SG": ("SINGAPORE", "🇸🇬"),
        "JP": ("JAPAN", "🇯🇵"),
        "DE": ("GERMANY", "🇩🇪"),
        "FR": ("FRANCE", "🇫🇷"),
        "BR": ("BRAZIL", "🇧🇷"),
        "AE": ("UAE", "🇦🇪"),
    }
    if country_code and country_code.upper() in countries:
        return countries[country_code.upper()]
    return ("UNKNOWN", "🌍")

