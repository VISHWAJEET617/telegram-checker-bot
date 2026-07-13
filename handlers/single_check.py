#!/usr/bin/env python3
"""Single Check - ₹10 PER CHECK (ONLY IF CARD WORKS)"""

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
    
    # Check balance (only if card will be ALIVE)
    balance = db.get_user_balance(user_id)
    
    # Processing
    msg = await message.answer(f"⏳ Checking: {card_num[:6]}****{card_num[-4:]}")
    
    try:
        # Check card
        card_info, status = await razorpay_gate.check_card_live(card_num, month, year, cvv)
        
        # ONLY CHARGE IF ALIVE (VALID CARD)
        if status == "ALIVE":
            if balance < 1000:
                await msg.edit_text(f"❌ Low balance: ₹{balance/100:.2f}\nNeed: ₹10")
                return
            
            # Deduct balance ONLY for ALIVE cards
            db.deduct_balance(user_id, 1000)
            
            # Log
            db.log_check(user_id, card_num[-4:], status, "Payment successful", 1000)
            
            response = format_response(card_info, status)
            await msg.edit_text(response)
            
            logger.info(f"✅ ALIVE: Charged ₹10")
        
        else:
            # DEAD - NO CHARGE
            db.log_check(user_id, card_num[-4:], status, card_info.get('response', 'Unknown'), 0)
            
            response = format_response(card_info, status)
            await msg.edit_text(response)
            
            logger.info(f"❌ DECLINED: No charge")
    
    except Exception as e:
        await msg.edit_text(f"❌ ERROR: {str(e)}")

def format_response(card_info: dict, status: str) -> str:
    """Format response"""
    
    if status == "ALIVE":
        charged = "💎 CHARGED\n💎 🟢 CHARGED 💎"
        price_text = "₹10"
    elif status == "DEAD":
        charged = "⚠️ DECLINED\n⚠️ ❌ DECLINED ⚠️"
        price_text = "FREE (No charge)"
    else:
        charged = "❌ ERROR\n❌ ❌ ERROR ❌"
        price_text = "FREE (No charge)"
    
    return f"""{charged}
━━━━━━━━━━━━━━━━━
💳 Card ➛ {card_info.get('card', 'UNKNOWN')}
📌 Gateway ➛ {card_info.get('gateway', 'RazorPay')}
📝 Response ➛ {card_info.get('response', 'Unknown')}
💰 Price ➛ {price_text}
━━━━━━━━━━━━━━━━━
🆔 BIN Information
├─ Brand ➛ {card_info.get('brand', 'UNKNOWN')}
├─ Type ➛ {card_info.get('type', 'UNKNOWN')}
├─ Level ➛ {card_info.get('level', 'UNKNOWN')}
├─ Bank ➛ {card_info.get('bank', 'UNKNOWN')}
└─ Country ➛ {card_info.get('country', 'UNKNOWN')}
━━━━━━━━━━━━━━━━━"""

