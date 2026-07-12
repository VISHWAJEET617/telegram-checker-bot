#!/usr/bin/env python3
"""Single Check - ₹10 PER CHECK with BIN info"""

import logging
import os
from aiogram import types
from gates.razorpay import RazorpayGate

logger = logging.getLogger(__name__)

razorpay_gate = RazorpayGate(
    key_id=os.getenv("RAZORPAY_KEY_ID"),
    key_secret=os.getenv("RAZORPAY_KEY_SECRET")
)

async def single_check_handler(message: types.Message, db):
    """Single card check - /rz CARD|MM|YY|CVV"""
    args = message.text.split(" ", 1)
    
    if len(args) < 2 or "|" not in args[1]:
        await message.answer("❌ Format: /rz CARD|MM|YY|CVV")
        return
    
    try:
        card_num, month, year, cvv = args[1].split("|")
    except:
        await message.answer("❌ Format: CARD|MM|YY|CVV")
        return
    
    user_id = message.from_user.id
    
    # Validate
    if not card_num.isdigit() or len(card_num) < 13:
        await message.answer("❌ Card invalid")
        return
    
    # Check balance
    balance = db.get_user_balance(user_id)
    if balance < 1000:
        await message.answer(f"❌ Low balance: ₹{balance/100:.2f}\nNeed: ₹10")
        return
    
    # Processing
    msg = await message.answer(f"⏳ Checking: {card_num[:6]}****{card_num[-4:]}")
    
    try:
        # Check card
        card_info, status = await razorpay_gate.check_card_live(card_num, month, year, cvv)
        
        # Deduct balance
        db.deduct_balance(user_id, 1000)
        
        # Log
        db.log_check(user_id, card_num[-4:], status, "Payment successful", 1000)
        
        # Format response
        response = format_response(card_info, status)
        await msg.edit_text(response)
        
        logger.info(f"✅ Check done: {status}")
    
    except Exception as e:
        await msg.edit_text(f"❌ ERROR: {str(e)}")

def format_response(card_info: dict, status: str) -> str:
    """Format response exactly as user wanted"""
    
    if status == "ALIVE":
        charged = "💎 CHARGED\n💎 🟢 CHARGED 💎"
    elif status == "DEAD":
        charged = "⚠️ DECLINED\n⚠️ ❌ DECLINED ⚠️"
    else:
        charged = "❌ ERROR\n❌ ❌ ERROR ❌"
    
    return f"""{charged}
━━━━━━━━━━━━━━━━━
💳 Card ➛ {card_info.get('card', 'UNKNOWN')}
📌 Gateway ➛ {card_info.get('gateway', 'RazorPay')}
📝 Response ➛ {card_info.get('response', 'Unknown')}
💰 Price ➛ {card_info.get('price', '₹10')}
━━━━━━━━━━━━━━━━━
🆔 BIN Information
├─ Brand ➛ {card_info.get('brand', 'UNKNOWN')}
├─ Type ➛ {card_info.get('type', 'UNKNOWN')}
├─ Level ➛ {card_info.get('level', 'UNKNOWN')}
├─ Bank ➛ {card_info.get('bank', 'UNKNOWN')}
└─ Country ➛ {card_info.get('country', 'UNKNOWN')}
━━━━━━━━━━━━━━━━━"""

