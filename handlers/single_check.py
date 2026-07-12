#!/usr/bin/env python3
"""
Single Check Handler - Single Card Verification (Production Level)
/rz command processor with real Razorpay validation
"""

import logging
import os
from aiogram import types
from utils import validate_card, format_card, get_card_brand, sanitize_input
from keyboards import help_keyboard, plans_keyboard
from gates.razorpay import RazorpayGate

logger = logging.getLogger(__name__)

# Initialize Razorpay gate
razorpay = RazorpayGate(
    key_id=os.getenv("RAZORPAY_KEY_ID"),
    key_secret=os.getenv("RAZORPAY_KEY_SECRET")
)

async def single_check_handler(message: types.Message, db):
    """Single card check command /rz"""
    args = message.text.split(" ", 1)
    
    if len(args) < 2:
        await message.answer(
            "❌ <b>Invalid format!</b>\n\n"
            "Usage: /rz CARD|MM|YY|CVV\n"
            "Example: /rz 4111111111111111|12|25|123\n\n"
            "Card Format:\n"
            "CARD - Card number (13-19 digits)\n"
            "MM - Month (01-12)\n"
            "YY - Year (2 digits, e.g., 25)\n"
            "CVV - Security code (3-4 digits)",
            reply_markup=help_keyboard()
        )
        return
    
    card = sanitize_input(args[1].strip())
    user_id = message.from_user.id
    
    # Validate card format (basic validation)
    is_valid, validation_msg = validate_card(card)
    
    if not is_valid:
        await message.answer(f"❌ <b>Validation Error</b>\n\n{validation_msg}")
        return
    
    # Check credits
    credits = db.get_user_credits(user_id)
    
    if credits < 1:
        await message.answer(
            "❌ <b>Insufficient Credits!</b>\n\n"
            "You need at least 1 credit to check a card.\n"
            f"Current credits: {credits}\n\n"
            "💳 Upgrade your plan:",
            reply_markup=plans_keyboard()
        )
        return
    
    # Extract card parts
    card_parts = card.split("|")
    card_num = card_parts[0]
    month = card_parts[1]
    year = card_parts[2]
    cvv = card_parts[3]
    
    card_brand = get_card_brand(card_num)
    formatted_card = format_card(card)
    card_last4 = card_num[-4:]
    
    # Show processing message
    processing_msg = await message.answer(
        f"⏳ <b>Checking card...</b>\n\n"
        f"{card_brand}\n"
        f"Card: {formatted_card}\n"
        f"Status: 🔄 Processing...\n"
        f"Credits used: 1\n\n"
        f"This may take 2-3 seconds..."
    )
    
    try:
        logger.info(f"Starting card check for user {user_id}: {card_num[:6]}****")
        
        # Perform PRODUCTION card validation via Razorpay
        result, status = await check_card_production(card_num, month, year, cvv)
        
        # Deduct credit
        db.update_credits(user_id, -1)
        new_credits = db.get_user_credits(user_id)
        
        # Log check
        db.log_check(user_id, card_last4, status, result, cost=1)
        
        # Update result message
        await processing_msg.edit_text(
            f"{card_brand} <b>Check Result</b>\n\n"
            f"Card: {formatted_card}\n"
            f"Result: {result}\n"
            f"Credits remaining: {new_credits}"
        )
        
        logger.info(f"Card check completed for user {user_id}: {status}")
    
    except Exception as e:
        logger.error(f"Card check error: {e}", exc_info=True)
        await message.answer(f"❌ <b>Error!</b>\n\n{str(e)}")

async def check_card_production(card_num: str, month: str, year: str, cvv: str) -> tuple:
    """
    PRODUCTION-LEVEL CARD VALIDATION
    
    Uses Razorpay API for real card validation
    
    Features:
    - Validates card BIN (first 6 digits)
    - Checks if card is active
    - Verifies expiry date
    - Detects card type (Visa, MC, Amex, Discover)
    - Handles errors gracefully
    
    Args:
        card_num: Full card number
        month: Expiry month (MM)
        year: Expiry year (YY)
        cvv: CVV code
    
    Returns:
        Tuple of (result_text, status) where status is ALIVE/DEAD/UNKNOWN/ERROR
    """
    try:
        logger.info(f"Production card check: {card_num[:6]}****")
        
        # Call real Razorpay validation
        result, status = await razorpay.check_card_live(card_num, month, year, cvv)
        
        return result, status
    
    except Exception as e:
        logger.error(f"Production check error: {e}", exc_info=True)
        return f"❌ <b>ERROR</b> - {str(e)}", "ERROR"

