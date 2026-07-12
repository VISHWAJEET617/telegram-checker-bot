#!/usr/bin/env python3
"""
Single Check Handler - Single Card Verification
/rz command processor
"""

from aiogram import types
from utils import validate_card, format_card, get_card_brand
from keyboards import help_keyboard, plans_keyboard

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
    
    card = args[1].strip()
    user_id = message.from_user.id
    
    # Validate card
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
    
    # Show processing message
    card_parts = card.split("|")
    card_brand = get_card_brand(card_parts[0])
    formatted_card = format_card(card)
    
    processing_msg = await message.answer(
        f"⏳ <b>Checking card...</b>\n\n"
        f"{card_brand}\n"
        f"Card: {formatted_card}\n"
        f"Status: 🔄 Processing...\n"
        f"Credits used: 1"
    )
    
    # Simulate check (in real scenario, call actual check API)
    try:
        # Deduct credit
        db.update_credits(user_id, -1)
        new_credits = db.get_user_credits(user_id)
        
        # Simulate result (replace with real API call)
        result = "✅ <b>ALIVE</b>"
        status = "ALIVE"
        
        # Log check
        db.log_check(user_id, card_parts[0][-4:], status, result, cost=1)
        
        # Update result message
        await processing_msg.edit_text(
            f"{card_brand} <b>Check Result</b>\n\n"
            f"Card: {formatted_card}\n"
            f"Result: {result}\n"
            f"Credits remaining: {new_credits}"
        )
    
    except Exception as e:
        await message.answer(f"❌ <b>Error!</b>\n\n{str(e)}")

