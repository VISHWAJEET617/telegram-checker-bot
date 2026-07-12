#!/usr/bin/env python3
"""
Keyboards Module - Telegram Inline Keyboards
All bot UI buttons and navigation
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def home_keyboard() -> InlineKeyboardMarkup:
    """Home screen keyboard with 4 main options"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")],
        [InlineKeyboardButton(text="🧪 Gates", callback_data="gates")],
        [InlineKeyboardButton(text="🪙 Plans", callback_data="plans")],
        [InlineKeyboardButton(text="❓ Help", callback_data="help")],
    ])

def profile_keyboard() -> InlineKeyboardMarkup:
    """Profile screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistics", callback_data="stats")],
        [InlineKeyboardButton(text="💳 Buy Credits", callback_data="buy_credits")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def gates_keyboard() -> InlineKeyboardMarkup:
    """Gates screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Razorpay", callback_data="razorpay")],
        [InlineKeyboardButton(text="🏦 Stripe", callback_data="stripe")],
        [InlineKeyboardButton(text="🔐 Auth Gate", callback_data="auth_gate")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def plans_keyboard() -> InlineKeyboardMarkup:
    """Plans screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Free Plan (25 credits)", callback_data="free_plan")],
        [InlineKeyboardButton(text="⭐ Premium (5000 credits)", callback_data="premium_plan")],
        [InlineKeyboardButton(text="💎 Diamond (Unlimited)", callback_data="diamond_plan")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def help_keyboard() -> InlineKeyboardMarkup:
    """Help screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Commands", callback_data="commands_help")],
        [InlineKeyboardButton(text="💬 Support", callback_data="support")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def back_button() -> InlineKeyboardMarkup:
    """Simple back button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def yes_no_keyboard() -> InlineKeyboardMarkup:
    """Yes/No keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes", callback_data="yes"),
            InlineKeyboardButton(text="❌ No", callback_data="no"),
        ],
    ])

def payment_keyboard() -> InlineKeyboardMarkup:
    """Payment keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Pay Now", callback_data="pay_now")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def confirmation_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
        ],
    ])

