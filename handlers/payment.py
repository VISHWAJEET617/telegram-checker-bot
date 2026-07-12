#!/usr/bin/env python3
"""
Payment Handler - UNLIMITED CREDITS
"""

import logging
from aiogram import types

logger = logging.getLogger(__name__)

async def payment_callback(callback: types.CallbackQuery, db, state):
    """Handle payment callbacks - UNLIMITED CREDITS"""
    plan_key = callback.data
    
    if plan_key == "plan_unlimited":
        user_id = callback.from_user.id
        
        # Set unlimited credits
        db.set_user_plan(user_id, "unlimited")
        
        await callback.message.edit_text(
            "∞ <b>Unlimited Credits Activated!</b>\n\n"
            "You now have UNLIMITED card checks\n\n"
            "Use /rz to check cards\n"
            "Use /help for commands"
        )
        
        logger.info(f"Unlimited plan activated for user {user_id}")
    else:
        await callback.answer("❌ Plan not available", show_alert=True)

async def razorpay_callback(callback: types.CallbackQuery, db, state):
    """Not used - Unlimited only"""
    await callback.answer("Unlimited plan active", show_alert=True)

