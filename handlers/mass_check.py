#!/usr/bin/env python3
"""
Mass Check Handler - Multiple Card Verification
/mrz command processor for batch checking
"""

import logging
import asyncio
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils import validate_card, parse_card_list, get_card_brand, sanitize_input
from keyboards import help_keyboard, plans_keyboard
from handlers.single_check import check_card

logger = logging.getLogger(__name__)

class MassCheckState(StatesGroup):
    waiting_for_file = State()

async def mass_check_handler(message: types.Message, db, state: FSMContext):
    """Mass card check command /mrz"""
    user_id = message.from_user.id
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    
    # Get max cards based on plan
    max_cards = {
        "free": 10,
        "premium": 100,
        "diamond": float('inf')
    }.get(plan, 10)
    
    if credits < (max_cards if max_cards != float('inf') else 100):
        await message.answer(
            f"❌ <b>Insufficient Credits!</b>\n\n"
            f"Your Plan: {plan.upper()}\n"
            f"Max Cards: {int(max_cards) if max_cards != float('inf') else 'Unlimited'}\n"
            f"Required Credits: {int(max_cards) if max_cards != float('inf') else 100}\n"
            f"Current Credits: {credits}\n\n"
            "💳 Upgrade your plan:",
            reply_markup=plans_keyboard()
        )
        return
    
    # Set state to wait for file
    await state.set_state(MassCheckState.waiting_for_file)
    
    await message.answer(
        "📤 <b>Mass Check Mode</b>\n\n"
        "Send a .txt file with cards (one per line)\n\n"
        "<b>Format:</b> CARD|MM|YY|CVV\n\n"
        "<b>Example:</b>\n"
        "4111111111111111|12|25|123\n"
        "5555555555554444|06|28|456\n"
        "378282246310005|10|27|789\n\n"
        f"Max cards per file: {int(max_cards) if max_cards != float('inf') else 'Unlimited'}\n\n"
        "Send /cancel to abort"
    )

async def process_mass_check_file(message: types.Message, db, state: FSMContext):
    """Process mass check file"""
    user_id = message.from_user.id
    
    # Check for cancel command
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Mass check cancelled")
        return
    
    # Validate it's a file
    if not message.document:
        await message.answer("❌ Please send a .txt file with cards")
        return
    
    # Validate file type
    if not message.document.file_name or not message.document.file_name.endswith('.txt'):
        await message.answer("❌ File must be .txt format")
        return
    
    # Validate file size (max 1MB)
    if message.document.file_size > 1024 * 1024:
        await message.answer("❌ File too large (max 1MB)")
        return
    
    try:
        plan = db.get_user_plan(user_id)
        max_cards = {
            "free": 10,
            "premium": 100,
            "diamond": float('inf')
        }.get(plan, 10)
        
        # Download file
        file_info = await message.bot.get_file(message.document.file_id)
        file = await message.bot.download_file(file_info.file_path)
        
        # Read and parse content
        content = file.read().decode('utf-8', errors='ignore')
        cards = parse_card_list(content)
        
        if not cards:
            await message.answer("❌ No valid cards found in file")
            await state.clear()
            return
        
        # Limit cards based on plan
        if len(cards) > max_cards and max_cards != float('inf'):
            await message.answer(
                f"⚠️ File contains {len(cards)} cards\n"
                f"Your plan allows max {int(max_cards)} cards\n"
                f"Processing first {int(max_cards)} cards only..."
            )
            cards = cards[:int(max_cards)]
        
        # Show confirmation
        await message.answer(
            f"📋 <b>File Details</b>\n\n"
            f"File: {message.document.file_name}\n"
            f"Cards found: {len(cards)}\n"
            f"Cost: {len(cards)} credits\n\n"
            f"Starting checks..."
        )
        
        # Process checks
        progress_msg = await message.answer(
            f"⏳ <b>Processing {len(cards)} cards...</b>\n\n"
            f"Status: Initializing...\n"
            f"Checked: 0/{len(cards)}"
        )
        
        # Deduct credits upfront
        db.update_credits(user_id, -len(cards))
        
        results = {
            "ALIVE": 0,
            "DEAD": 0,
            "UNKNOWN": 0,
            "ERROR": 0
        }
        
        errors = []
        
        # Check each card
        for idx, card in enumerate(cards, 1):
            try:
                # Validate card format
                is_valid, _ = validate_card(card)
                if not is_valid:
                    results["ERROR"] += 1
                    errors.append(f"Card {idx}: Invalid format")
                    continue
                
                # Extract card parts
                parts = card.split("|")
                result_text, status = await check_card(parts[0], parts[1], parts[2], parts[3])
                
                results[status] += 1
                
                # Log check
                db.log_check(user_id, parts[0][-4:], status, result_text, cost=1)
                
                # Update progress every 5 cards
                if idx % 5 == 0:
                    await progress_msg.edit_text(
                        f"⏳ <b>Processing {len(cards)} cards...</b>\n\n"
                        f"Status: Running...\n"
                        f"Checked: {idx}/{len(cards)}\n\n"
                        f"✅ ALIVE: {results['ALIVE']}\n"
                        f"❌ DEAD: {results['DEAD']}\n"
                        f"⚠️ UNKNOWN: {results['UNKNOWN']}"
                    )
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing card {idx}: {e}")
                results["ERROR"] += 1
                errors.append(f"Card {idx}: {str(e)}")
        
        # Final results
        remaining_credits = db.get_user_credits(user_id)
        
        results_text = (
            f"✅ <b>Mass Check Complete!</b>\n\n"
            f"📊 <b>Results:</b>\n"
            f"✅ ALIVE: {results['ALIVE']}\n"
            f"❌ DEAD: {results['DEAD']}\n"
            f"⚠️ UNKNOWN: {results['UNKNOWN']}\n"
            f"💥 ERRORS: {results['ERROR']}\n\n"
            f"💳 Credits used: {len(cards)}\n"
            f"💳 Remaining: {remaining_credits}"
        )
        
        if errors and len(errors) <= 10:
            results_text += "\n\n<b>Errors:</b>\n" + "\n".join(errors[:10])
        
        await progress_msg.edit_text(results_text)
        
        # Clear state
        await state.clear()
        
        logger.info(f"Mass check completed for user {user_id}: {len(cards)} cards")
    
    except Exception as e:
        logger.error(f"Mass check error: {e}")
        await message.answer(f"❌ <b>Error processing file!</b>\n\n{str(e)}")
        await state.clear()

