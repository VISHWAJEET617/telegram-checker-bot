#!/usr/bin/env python3
"""
Utils Module - Utility Functions
Card validation, formatting, and helper functions
"""

import re
import logging

logger = logging.getLogger(__name__)

def validate_card(card_string: str) -> tuple[bool, str]:
    """
    Validate card format
    Expected format: CARD|MM|YY|CVV
    Example: 4111111111111111|12|25|123
    """
    try:
        parts = card_string.strip().split("|")
        
        if len(parts) != 4:
            return False, "❌ Invalid format! Use: CARD|MM|YY|CVV"
        
        card_num, mm, yy, cvv = parts
        
        # Validate card number
        if not card_num.isdigit():
            return False, "❌ Card number must contain only digits"
        
        if len(card_num) < 13 or len(card_num) > 19:
            return False, "❌ Card number must be 13-19 digits"
        
        # Luhn algorithm check
        if not luhn_check(card_num):
            return False, "❌ Invalid card number (Luhn check failed)"
        
        # Validate month
        if not mm.isdigit():
            return False, "❌ Month must be numeric"
        
        month = int(mm)
        if month < 1 or month > 12:
            return False, "❌ Month must be 01-12"
        
        # Validate year
        if not yy.isdigit() or len(yy) != 2:
            return False, "❌ Year must be 2 digits (YY)"
        
        # Validate CVV
        if not cvv.isdigit():
            return False, "❌ CVV must be numeric"
        
        if len(cvv) != 3 and len(cvv) != 4:
            return False, "❌ CVV must be 3 or 4 digits"
        
        return True, "✅ Valid card format"
    
    except Exception as e:
        logger.error(f"Card validation error: {e}")
        return False, f"❌ Error validating card: {str(e)}"

def luhn_check(card_num: str) -> bool:
    """
    Luhn algorithm for card number validation
    """
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_num)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    
    return checksum % 10 == 0

def format_card(card_string: str) -> str:
    """
    Format card for display
    Example: 411111****1111 | 12/25
    """
    try:
        parts = card_string.split("|")
        if len(parts) == 4:
            card_num, mm, yy, cvv = parts
            return f"{card_num[:6]}****{card_num[-4:]} | {mm}/{yy}"
        return card_string
    except Exception as e:
        logger.error(f"Card formatting error: {e}")
        return card_string

def format_card_safe(card_string: str) -> str:
    """
    Format card number safely (show only last 4 digits)
    """
    try:
        card_num = card_string.split("|")[0] if "|" in card_string else card_string
        return f"****{card_num[-4:]}"
    except Exception as e:
        logger.error(f"Safe card formatting error: {e}")
        return "****XXXX"

def is_valid_telegram_id(user_id: int) -> bool:
    """Check if user ID is valid"""
    return isinstance(user_id, int) and user_id > 0

def is_valid_username(username: str) -> bool:
    """Check if username is valid"""
    if not username:
        return False
    return re.match(r'^[a-zA-Z0-9_]{3,32}$', username) is not None

def parse_card_list(text: str) -> list[str]:
    """
    Parse card list from text
    One card per line in format CARD|MM|YY|CVV
    """
    cards = []
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):  # Skip empty lines and comments
            cards.append(line)
    return cards

def get_card_brand(card_num: str) -> str:
    """
    Detect card brand from card number
    """
    if card_num.startswith('4'):
        return "🟦 Visa"
    elif card_num.startswith('5'):
        return "🟥 Mastercard"
    elif card_num.startswith('3'):
        return "🟩 Amex"
    elif card_num.startswith('6'):
        return "🟨 Discover"
    else:
        return "💳 Unknown"

def format_credits(credits: int) -> str:
    """Format credits with emoji"""
    if credits >= 5000:
        return f"💎 {credits}"
    elif credits >= 100:
        return f"⭐ {credits}"
    elif credits >= 25:
        return f"🎁 {credits}"
    else:
        return f"❌ {credits}"

def get_plan_emoji(plan: str) -> str:
    """Get emoji for plan"""
    plans = {
        "free": "🎁",
        "premium": "⭐",
        "diamond": "💎"
    }
    return plans.get(plan.lower(), "❓")

def truncate_text(text: str, length: int = 100) -> str:
    """Truncate text to length"""
    if len(text) > length:
        return text[:length] + "..."
    return text

def format_timestamp(timestamp) -> str:
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        return timestamp.split()[0]  # Return just date part
    return str(timestamp)

