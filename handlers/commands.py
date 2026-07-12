#!/usr/bin/env python3
"""
Commands Handler - All Command Processors
/help, /cmds, /stats, /profile handlers
"""

from aiogram import types
from keyboards import help_keyboard

async def help_handler(message: types.Message):
    """Help command handler"""
    help_text = (
        "<b>📖 Help & Commands</b>\n\n"
        "/start - Home menu\n"
        "/help - This help message\n"
        "/cmds - All commands\n"
        "/profile - Your profile\n"
        "/rz - Single card check\n"
        "/mrz - Mass card check\n\n"
        "Format: /rz 4111111111111111|12|25|123\n\n"
        "Card Format: CARD|MM|YY|CVV\n"
        "Example: 4111111111111111|12|25|123"
    )
    await message.answer(help_text, reply_markup=help_keyboard())

async def cmds_handler(message: types.Message):
    """Commands list handler"""
    cmds_text = (
        "<b>📝 All Commands</b>\n\n"
        "<b>Main Commands:</b>\n"
        "/start - Home\n"
        "/help - Help\n"
        "/profile - Profile\n"
        "/cmds - This message\n\n"
        "<b>Checking Commands:</b>\n"
        "/rz CARD|MM|YY|CVV - Single check\n"
        "/mrz - Mass check mode\n\n"
        "<b>Info Commands:</b>\n"
        "/stats - Your statistics\n"
        "/plans - Available plans\n"
        "/support - Get support"
    )
    await message.answer(cmds_text)

async def stats_handler(message: types.Message, db):
    """Statistics handler"""
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    
    stats_text = (
        "<b>📊 Your Statistics</b>\n\n"
        f"<b>Plan:</b> {plan.upper()}\n"
        f"<b>Credits:</b> {credits}\n"
        f"<b>Total Checks:</b> {stats['total_checks']}\n"
        f"<b>Alive Cards:</b> {stats['alive_checks']}\n"
        f"<b>Total Spent:</b> {stats['total_spent']}"
    )
    
    await message.answer(stats_text)

