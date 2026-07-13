#!/usr/bin/env python3
"""Single Card Check - /rz with exact UI"""

import logging
import os
import asyncio
from aiogram import types
from gates.razorpay import RazorpayGate

logger = logging.getLogger(__name__)

razorpay_gate = RazorpayGate(
    key_id=os.getenv("RAZORPAY_KEY_ID", ""),
    key_secret=os.getenv("RAZORPAY_KEY_SECRET", "")
)

async def single_check_handler(message: types.Message, db):
    """Single card check - /rz CARD|MM|YY|CVV"""
    args = message.text.split(" ", 1)
    
    if len(args) < 2 or "|" not in args[1]:
        await message.answer("❌ Format: /rz CARD|MM|YY|CVV")
        return
    
    try:
        card_data = args[1].strip()
        parts = card_data.split("|")
        if len(parts) != 4:
            raise ValueError("Invalid format")
        card_num, month, year, cvv = parts
    except:
        await message.answer("❌ Format: CARD|MM|YY|CVV")
        return
    
    user_id = message.from_user.id
    
    # Validate card
    if not card_num.isdigit() or len(card_num) < 13:
        await message.answer("❌ Card invalid")
        return
    
    if not month.isdigit() or not (1 <= int(month) <= 12):
        await message.answer("❌ Invalid month (01-12)")
        return
    
    if not year.isdigit() or len(year) != 2:
        await message.answer("❌ Invalid year (YY format)")
        return
    
    if not cvv.isdigit() or len(cvv) not in [3, 4]:
        await message.answer("❌ Invalid CVV")
        return
    
    # Check balance
    balance = db.get_user_balance(user_id)
    if balance < 1000:
        await message.answer(f"❌ Insufficient balance: ₹{balance/100:.2f}")
        return
    
    # Show processing
    msg = await message.answer(f"⏳ Checking: {card_num[:6]}****{card_num[-4:]}")
    
    try:
        # Check card with Razorpay
        card_info, status = await razorpay_gate.check_card_live(card_num, month, year, cvv)
        
        # Only charge if ALIVE
        if status == "ALIVE":
            # Deduct balance
            db.deduct_balance(user_id, 1000)
            
            # Log transaction
            db.log_check(user_id, card_num[-4:], status, "Payment Successfully", 1000)
            
            # Format response - CHARGED
            response = f"""💎 🟢 CHARGED 💎
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
━━━━━━━━━━━━━━━━━"""
            
            logger.info(f"✅ CHARGED: {user_id} | {card_num[-4:]} | ₹10")
        
        else:
            # DECLINED - NO CHARGE
            # Log transaction (cost=0)
            db.log_check(user_id, card_num[-4:], status, "Card Declined", 0)
            
            # Format response - DECLINED
            response = f"""💎 🔴 DECLINED 💎
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
━━━━━━━━━━━━━━━━━"""
            
            logger.info(f"❌ DECLINED: {user_id} | {card_num[-4:]} | FREE")
        
        # Update message with result
        await msg.edit_text(response)
    
    except Exception as e:
        logger.error(f"Error checking card: {str(e)}")
        await msg.edit_text(f"❌ Error: {str(e)}")

