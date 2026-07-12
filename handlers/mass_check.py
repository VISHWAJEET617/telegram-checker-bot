#!/usr/bin/env python3
"""
Mass Check Handler - Multiple Card Verification
/mrz command processor for batch checking
"""

from aiogram import types
from utils import validate_card, parse_card_list, get_card_brand
from keyboards import help_keyboard, plans_keyboard

async def mass_check_handler(message: types.Message, db, state):
    """Mass card check command /mrz"""
    user_id = message.from_user.id
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    
    # Get max cards based on plan
    max_cards = {
        "free": 10,
        "premium": 100,
        "diamond": 1000
    }.get(plan, 10)
    
    if credits < max_cards:
        await message.answer(
            f"❌ <b>Insufficient Credits!</b>\n\n"
            f"Your Plan: {plan.upper()}\n"
            f"Max Cards: {max_cards}\n"
            f"Required Credits: {max_cards}\n"
            f"Current Credits: {credits}\n\n"
            "💳 Upgrade your plan:",
            reply_markup=plans_keyboard()
        )
        return
    
    # Set state to wait for file
    await message.answer(
        "<b>📤 Mass Check Mode</b>\n\n"
        "Send a .txt file with cards (one per line)\n\n"
        "<b>Format:</b> CARD|MM|YY|CVV\n\n"
        "<b>Example:</b>\n"
        "4111111111111111|12|25|123\n"
        "5555555555554444|06|28|456\n"
        "378282246310005|10|27|789\n\n"
        f"Max cards per file: {max_cards}"
    )

async def process_mass_check_file(message: types.Message, db):
    """Process mass check file"""
    user_id = message.from_user.id
    
    if not message.document or not message.document.file_name.endswith('.txt'):
        await message.answer("❌ Please send a .txt file")
        return
    
    try:
        # Get file
        file_info = await message.bot.get_file(message.document.file_id)
        file_path = file_info.file_path
        
        # Download file (in real scenario)
        # For now, just show message
        
        plan = db.get_user_plan(user_id)
        max_cards = {
            "free": 10,
            "premium": 100,
            "diamond": 1000
        }.get(plan, 10)
        
        await message.answer(
            f"✅ <b>File Received</b>\n\n"
            f"File: {message.document.file_name}\n"
            f"File Size: {message.document.file_size} bytes\n\n"
            f"Starting checks...\n"
            f"Max cards: {max_cards}\n\n"
            f"This may take a while. You'll be notified when done."
        )
        
        # Deduct credits
        db.update_credits(user_id, -max_cards)
        
        await message.answer(
            f"💳 Credits deducted: {max_cards}\n"
            f"Remaining: {db.get_user_credits(user_id)}"
        )
    
    except Exception as e:
        await message.answer(f"❌ Error processing file: {str(e)}")

