#!/usr/bin/env python3
"""
Keyboards Module - UNLIMITED CREDITS
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def home_keyboard() -> InlineKeyboardMarkup:
    """Home screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")],
        [InlineKeyboardButton(text="❓ Help", callback_data="help")],
    ])

def profile_keyboard() -> InlineKeyboardMarkup:
    """Profile screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistics", callback_data="stats")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def help_keyboard() -> InlineKeyboardMarkup:
    """Help screen keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Commands", callback_data="commands_help")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def back_button() -> InlineKeyboardMarkup:
    """Simple back button"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

def plans_keyboard() -> InlineKeyboardMarkup:
    """UNLIMITED CREDITS"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="∞ Unlimited Credits", callback_data="plan_unlimited")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")],
    ])

