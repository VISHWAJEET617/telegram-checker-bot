#!/usr/bin/env python3
"""
Single Check Handler - UNLIMITED CREDITS
Real card validation via Razorpay, REAL CHARGES
"""

import logging
import os
from aiogram import types
from utils import validate_card, format_card, get_card_brand, sanitize_input
from keyboards import help_keyboard, plans_keyboard
from gates.razorpay import RazorpayGate

logger = logging.getLogger(__name__)

# Initialize Razorpay PRODUCTION gateway
try:
    razorpay = RazorpayGate(
        key_id=os.getenv("RAZORPAY_KEY_ID"),
        key_secret=os.getenv("RAZORPAY_KEY_SECRET")
    )
except ValueError as e:
    logger.critical(f"❌ PRODUCTION ERROR: {e}")
    raise

async def single_check_handler(message: types.Message, db):
    """Single card check command /rz - UNLIMITED CREDITS"""
    args = message.text.split(" ", 1)
    
    if len(args) < 2:
        await message.answer(
            "❌ <b>Invalid format!</b>\n\n"
            "Usage: /rz CARD|MM|YY|CVV\n"
            "Example: /rz 4111111111111111|12|25|123",
            reply_markup=help_keyboard()
        )
        return
    
    card = sanitize_input(args[1].strip())
    user_id = message.from_user.id
    
    # Validate card format
    is_valid, validation_msg = validate_card(card)
    
    if not is_valid:
        await message.answer(f"❌ <b>Validation Error</b>\n\n{validation_msg}")
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
        f"⏳ <b>Validating card via Razorpay...</b>\n\n"
        f"{card_brand}\n"
        f"Card: {formatted_card}\n"
        f"Status: 🔄 Processing...\n\n"
        f"<i>Real validation in progress...</i>"
    )
    
    try:
        logger.info(f"PRODUCTION: Card check user={user_id}, card={card_num[:6]}****")
        
        # PRODUCTION: Call real Razorpay validation
        result, status = await check_card_production(card_num, month, year, cvv)
        
        # Log to database (unlimited credits - no deduction)
        db.log_check(user_id, card_last4, status, result, cost=0)
        
        # Send result
        await processing_msg.edit_text(
            f"{card_brand} <b>Validation Result</b>\n\n"
            f"Card: {formatted_card}\n"
            f"Result: {result}\n\n"
            f"∞ <b>Unlimited checks available</b>"
        )
        
        logger.info(f"PRODUCTION: Check complete - user={user_id}, status={status}")
    
    except Exception as e:
        logger.error(f"❌ PRODUCTION ERROR: {e}", exc_info=True)
        await message.answer(f"❌ <b>Validation Error</b>\n\n{str(e)}")

async def check_card_production(card_num: str, month: str, year: str, cvv: str) -> tuple:
    """PRODUCTION ONLY: Real Razorpay card validation"""
    try:
        result, status = await razorpay.check_card_live(card_num, month, year, cvv)
        return result, status
    
    except Exception as e:
        logger.error(f"❌ PRODUCTION CHECK ERROR: {e}")
        return f"❌ <b>ERROR</b> - {str(e)}", "ERROR"

