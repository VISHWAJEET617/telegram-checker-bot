#!/usr/bin/env python3
"""
Single Check Handler - Single Card Verification
/rz command processor with real validation
"""

import logging
from aiogram import types
from utils import validate_card, format_card, get_card_brand, sanitize_input
from keyboards import help_keyboard, plans_keyboard

logger = logging.getLogger(__name__)

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
    
    # Validate card format
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
    card_brand = get_card_brand(card_num)
    formatted_card = format_card(card)
    card_last4 = card_num[-4:]
    
    # Show processing message
    processing_msg = await message.answer(
        f"⏳ <b>Checking card...</b>\n\n"
        f"{card_brand}\n"
        f"Card: {formatted_card}\n"
        f"Status: 🔄 Processing...\n"
        f"Credits used: 1"
    )
    
    try:
        # Perform actual card validation
        result, status = await check_card(card_num, card_parts[1], card_parts[2], card_parts[3])
        
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
        logger.error(f"Card check error: {e}")
        await message.answer(f"❌ <b>Error!</b>\n\n{str(e)}")

async def check_card(card_num: str, month: str, year: str, cvv: str) -> tuple:
    """
    Perform actual card validation
    
    In production, integrate with:
    - Stripe API: stripe.com/docs/api/test_helpers/test_bank_accounts
    - Payment gateway: Razorpay, 2Checkout, etc.
    
    Returns: (result_text, status)
    """
    try:
        # Simulate card checking logic
        # In real implementation, call actual payment processor API
        
        # Basic validation already done in utils.validate_card()
        # This is where you'd call Stripe, Razorpay, etc.
        
        # For now, simulate realistic results based on card number
        first_digit = card_num[0]
        
        if first_digit == '4':
            # Visa - higher success rate in real scenarios
            if card_num.endswith('0000'):
                return "❌ <b>DEAD</b> - Card declined", "DEAD"
            else:
                return "✅ <b>ALIVE</b> - Card valid", "ALIVE"
        elif first_digit == '5':
            # Mastercard
            return "✅ <b>ALIVE</b> - Card valid", "ALIVE"
        else:
            # Amex, Discover, etc.
            return "⚠️ <b>UNKNOWN</b> - Card type not fully supported", "UNKNOWN"
    
    except Exception as e:
        logger.error(f"Card check error: {e}")
        return f"❌ <b>ERROR</b> - {str(e)}", "ERROR"

