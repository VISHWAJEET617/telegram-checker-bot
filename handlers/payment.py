#!/usr/bin/env python3
"""
Payment Handler - FREE PLAN ONLY
No Premium/Diamond
"""

import logging
from aiogram import types

logger = logging.getLogger(__name__)

async def payment_callback(callback: types.CallbackQuery, db, state):
    """Handle payment callbacks - FREE PLAN ONLY"""
    plan_key = callback.data
    
    if plan_key == "plan_free":
        user_id = callback.from_user.id
        
        # Add free credits
        db.set_user_plan(user_id, "free")
        db.update_credits(user_id, 25)
        
        await callback.message.edit_text(
            "🎁 <b>Free Plan Activated!</b>\n\n"
            "You now have 25 free credits\n\n"
            "Use /rz to check cards\n"
            "Use /help for commands"
        )
        
        logger.info(f"Free plan activated for user {user_id}")
    else:
        await callback.answer("❌ Plan not available", show_alert=True)

async def razorpay_callback(callback: types.CallbackQuery, db, state):
    """Razorpay callback - NOT USED (Free plan only)"""
    await callback.answer("Premium plans coming soon", show_alert=True)

