#!/usr/bin/env python3
"""
Start Handler - Home Screen Handler
Handles /start command and home navigation
"""

from aiogram import types
from keyboards import home_keyboard

async def start_handler(message: types.Message, owner_name: str, developer_name: str):
    """Start command handler"""
    welcome_text = (
        f"🎉 <b>Welcome to Telegram Premium Checker Bot!</b>\n\n"
        f"👤 Hello <b>{message.from_user.first_name}</b>\n\n"
        f"Select an option below to get started.\n\n"
        f"<i>Owner: {owner_name}</i>\n"
        f"<i>Developer: {developer_name}</i>"
    )
    
    await message.answer(welcome_text, reply_markup=home_keyboard())

