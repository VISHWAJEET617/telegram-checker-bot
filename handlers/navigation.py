#!/usr/bin/env python3
"""
Navigation Handler - Screen Navigation
Callback query handlers for menu navigation
"""

import logging
from aiogram import types
from keyboards import (
    home_keyboard, profile_keyboard, gates_keyboard,
    plans_keyboard, help_keyboard
)

logger = logging.getLogger(__name__)

async def profile_callback(callback: types.CallbackQuery, db):
    """Profile screen callback"""
    user_id = callback.from_user.id
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    stats = db.get_user_stats(user_id)
    
    profile_text = (
        "<b>👤 Your Profile</b>\n\n"
        f"<b>User ID:</b> {user_id}\n"
        f"<b>Username:</b> @{callback.from_user.username or 'Unknown'}\n"
        f"<b>First Name:</b> {callback.from_user.first_name}\n"
        f"<b>Credits:</b> {credits}\n"
        f"<b>Plan:</b> {plan.upper()}\n"
        f"<b>Total Checks:</b> {stats['total_checks']}\n"
        f"<b>Alive Cards:</b> {stats['alive_checks']}\n"
        f"<b>Status:</b> ✅ Active"
    )
    
    await callback.message.edit_text(profile_text, reply_markup=profile_keyboard())
    await callback.answer()

async def gates_callback(callback: types.CallbackQuery):
    """Gates screen callback"""
    gates_text = (
        "<b>🧪 Available Gates</b>\n\n"
        "1. <b>Razorpay Gate</b>\n"
        "   Indian payment gateway\n"
        "   Status: ✅ Active\n\n"
        "2. <b>Stripe Gate</b>\n"
        "   Global payment gateway\n"
        "   Status: ⏳ Coming Soon\n\n"
        "3. <b>Auth Gate</b>\n"
        "   Custom authentication\n"
        "   Status: ⏳ Coming Soon"
    )
    
    await callback.message.edit_text(gates_text, reply_markup=gates_keyboard())
    await callback.answer()

async def plans_callback(callback: types.CallbackQuery):
    """Plans screen callback"""
    plans_text = (
        "<b>🪙 Plans & Pricing</b>\n\n"
        "<b>🎁 Free Plan</b>\n"
        "   Credits: 25\n"
        "   Single Check: ✅\n"
        "   Mass Check: ❌ (Limited to 10 cards)\n\n"
        "<b>⭐ Premium Plan</b>\n"
        "   Credits: 5000\n"
        "   Single Check: ✅\n"
        "   Mass Check: ✅ (100 cards/check)\n\n"
        "<b>💎 Diamond Plan</b>\n"
        "   Credits: Unlimited\n"
        "   Single Check: ✅\n"
        "   Mass Check: ✅ (Unlimited)"
    )
    
    await callback.message.edit_text(plans_text, reply_markup=plans_keyboard())
    await callback.answer()

async def help_callback(callback: types.CallbackQuery):
    """Help screen callback"""
    help_text = (
        "<b>❓ Help & Support</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Home menu\n"
        "/profile - Your profile\n"
        "/rz CARD|MM|YY|CVV - Single check\n"
        "/mrz - Mass check\n"
        "/cmds - All commands\n\n"
        "<b>Card Format:</b>\n"
        "CARD|MM|YY|CVV\n"
        "Example: 4111111111111111|12|25|123\n\n"
        "<b>Support:</b>\n"
        "Contact: @support_bot"
    )
    
    await callback.message.edit_text(help_text, reply_markup=help_keyboard())
    await callback.answer()

async def back_callback(callback: types.CallbackQuery):
    """Back to home callback"""
    welcome_text = (
        "<b>🎉 Telegram Premium Checker Bot</b>\n\n"
        "Select an option below."
    )
    
    await callback.message.edit_text(welcome_text, reply_markup=home_keyboard())
    await callback.answer()

