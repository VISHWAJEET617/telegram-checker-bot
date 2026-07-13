#!/usr/bin/env python3
"""Batch Card Check - /mrz with exact UI"""

import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from gates.razorpay import RazorpayGate
import os

logger = logging.getLogger(__name__)

razorpay_gate = RazorpayGate(
    key_id=os.getenv("RAZORPAY_KEY_ID", ""),
    key_secret=os.getenv("RAZORPAY_KEY_SECRET", "")
)


class BatchCheckState(StatesGroup):
    """Batch check mode states"""
    waiting_for_cards = State()


async def batch_check_start(message: types.Message, state: FSMContext, db):
    """Start batch check mode - /mrz"""
    
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    # Enter batch mode
    await state.set_state(BatchCheckState.waiting_for_cards)
    await state.update_data(
        cards_checked=[],
        total_charged=0,
        alive_count=0,
        declined_count=0,
        user_id=user_id
    )
    
    await message.answer(f"""
📋 BATCH CHECK MODE STARTED

Balance: ₹{balance/100:.2f}

Send cards one by one:
Format: CARD|MM|YY|CVV

Example:
5306908108485578|02|30|407
4403934994847346|04|28|712

Send /done when finished
Send /cancel to exit
""")


async def batch_card_handler(message: types.Message, state: FSMContext, db):
    """Handle individual card in batch mode"""
    
    # Check if in batch mode
    current_state = await state.get_state()
    if current_state != BatchCheckState.waiting_for_cards.state:
        return
    
    # Handle /done command
    if message.text.lower() == "/done":
        await batch_check_complete(message, state, db)
        return
    
    # Handle /cancel command
    if message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("❌ Batch check cancelled")
        return
    
    # Parse card
    try:
        parts = message.text.strip().split("|")
        if len(parts) != 4:
            raise ValueError("Invalid format")
        card_num, month, year, cvv = parts
    except:
        await message.answer("❌ Invalid format. Use: CARD|MM|YY|CVV")
        return
    
    if not card_num.isdigit() or len(card_num) < 13:
        await message.answer("❌ Card invalid")
        return
    
    # Get data from state
    data = await state.get_data()
    user_id = data["user_id"]
    balance = db.get_user_balance(user_id)
    card_count = len(data["cards_checked"]) + 1
    
    # Show processing
    msg = await message.answer(f"⏳ Card {card_count}: Checking {card_num[:6]}****{card_num[-4:]}...")
    
    try:
        # Check card
        card_info, status = await razorpay_gate.check_card_live(card_num, month, year, cvv)
        
        # Only charge if ALIVE
        if status == "ALIVE":
            if balance < 1000:
                await msg.edit_text(f"❌ Low balance: ₹{balance/100:.2f}\nNeed: ₹10")
                return
            
            # Charge
            db.deduct_balance(user_id, 1000)
            db.log_check(user_id, card_num[-4:], status, "Payment Successfully", 1000)
            balance -= 1000
            
            # Format response - CHARGED
            response = f"""✅ Card {card_count} - ALIVE ✅
💎 🟢 CHARGED 💎
━━━━━━━━━━━━━━━━━
💳 Card ➛ {card_num}|{month}|{year}|{cvv}
📌 Gateway ➛ RazorPay
📝 Response ➛ Payment Successfully
💰 Price ➛ ₹10
━━━━━━━━━━━━━━━━━
🆔 BIN Information
├─ Brand ➛ {card_info['brand']}
├─ Type ➛ {card_info['type']}
├─ Level ➛ {card_info['level']}
├─ Bank ➛ {card_info['bank']}
└─ Country ➛ {card_info['country']}
━━━━━━━━━━━━━━━━━

Ready for next card... (/done to finish)
"""
            
            # Update counters
            data["cards_checked"].append({
                "card": card_num[-4:],
                "status": "ALIVE",
                "charge": 10
            })
            data["total_charged"] += 10
            data["alive_count"] += 1
        
        else:
            # DECLINED - NO CHARGE
            db.log_check(user_id, card_num[-4:], status, "Card Declined", 0)
            
            # Format response - DECLINED
            response = f"""❌ Card {card_count} - DECLINED ❌
💎 🔴 DECLINED 💎
━━━━━━━━━━━━━━━━━
💳 Card ➛ {card_num}|{month}|{year}|{cvv}
📌 Gateway ➛ RazorPay
📝 Response ➛ Card Declined
💰 Price ➛ ₹10
━━━━━━━━━━━━━━━━━
🆔 BIN Information
├─ Brand ➛ {card_info['brand']}
├─ Type ➛ {card_info['type']}
├─ Level ➛ {card_info['level']}
├─ Bank ➛ {card_info['bank']}
└─ Country ➛ {card_info['country']}
━━━━━━━━━━━━━━━━━

Ready for next card... (/done to finish)
"""
            
            # Update counters
            data["cards_checked"].append({
                "card": card_num[-4:],
                "status": "DECLINED",
                "charge": 0
            })
            data["declined_count"] += 1
        
        # Update state
        await state.update_data(data)
        await msg.edit_text(response)
        
    except Exception as e:
        logger.error(f"Error checking card: {str(e)}")
        await msg.edit_text(f"❌ Error: {str(e)}")


async def batch_check_complete(message: types.Message, state: FSMContext, db):
    """Complete batch check and show summary"""
    
    data = await state.get_data()
    user_id = data["user_id"]
    
    # Get final balance
    final_balance = db.get_user_balance(user_id)
    
    # Build summary
    summary = f"""
📊 BATCH CHECK COMPLETE
━━━━━━━━━━━━━━━━━━━━

Total Cards: {len(data['cards_checked'])}
✅ Alive: {data['alive_count']}
❌ Declined: {data['declined_count']}

💰 Total Charged: ₹{data['total_charged']}

Final Balance: ₹{final_balance/100:.2f}
━━━━━━━━━━━━━━━━━━━━

Cards:
"""
    
    for i, card in enumerate(data["cards_checked"], 1):
        if card["status"] == "ALIVE":
            summary += f"\n{i}. {card['card']} - ✅ ALIVE (+₹{card['charge']})"
        else:
            summary += f"\n{i}. {card['card']} - ❌ DECLINED (FREE)"
    
    await state.clear()
    await message.answer(summary)

