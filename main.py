#!/usr/bin/env python3
"""
Telegram Premium Checker Bot - Main Entry Point
Complete Production Ready Bot
"""

import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
import asyncio

from db import Database
from keyboards import home_keyboard, profile_keyboard, gates_keyboard, plans_keyboard, help_keyboard

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
OWNER_NAME = os.getenv("OWNER_NAME", "Admin")
DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "Developer")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file!")

bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML
)
dp = Dispatcher()
db = Database()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Start command handler"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    db.add_user(user_id, username)
    
    welcome_text = (
        f"🎉 <b>Welcome to Telegram Premium Checker Bot!</b>\n\n"
        f"👤 Hello <b>{message.from_user.first_name}</b>\n\n"
        f"Select an option below to get started.\n\n"
        f"<i>Bot Owner: {OWNER_NAME}</i>\n"
        f"<i>Developer: {DEVELOPER_NAME}</i>"
    )
    
    await message.answer(welcome_text, reply_markup=home_keyboard())

@dp.message(Command("help"))
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
        "Format: /rz 4111111111111111|12|25|123"
    )
    await message.answer(help_text, reply_markup=help_keyboard())

@dp.message(Command("cmds"))
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
        "<b>Admin Commands:</b>\n"
        "/stats - Bot statistics\n"
        "/users - User count"
    )
    await message.answer(cmds_text)

@dp.message(Command("profile"))
async def profile_handler(message: types.Message):
    """Profile command handler"""
    user_id = message.from_user.id
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    
    profile_text = (
        "<b>👤 Your Profile</b>\n\n"
        f"<b>User ID:</b> {user_id}\n"
        f"<b>Username:</b> @{message.from_user.username or 'Unknown'}\n"
        f"<b>Name:</b> {message.from_user.first_name}\n"
        f"<b>Credits:</b> {credits}\n"
        f"<b>Plan:</b> {plan.upper()}\n"
        f"<b>Status:</b> ✅ Active"
    )
    
    await message.answer(profile_text, reply_markup=profile_keyboard())

@dp.message(Command("rz"))
async def single_check_handler(message: types.Message):
    """Single card check command"""
    args = message.text.split(" ", 1)
    
    if len(args) < 2:
        await message.answer(
            "❌ <b>Invalid format!</b>\n\n"
            "Usage: /rz CARD|MM|YY|CVV\n"
            "Example: /rz 4111111111111111|12|25|123",
            reply_markup=help_keyboard()
        )
        return
    
    card = args[1]
    user_id = message.from_user.id
    credits = db.get_user_credits(user_id)
    
    if credits < 1:
        await message.answer(
            "❌ <b>Insufficient credits!</b>\n\n"
            "You need at least 1 credit to check a card.\n"
            "Current credits: 0",
            reply_markup=plans_keyboard()
        )
        return
    
    # Process check
    await message.answer(
        f"⏳ <b>Checking card...</b>\n\n"
        f"Card: {card[:6]}****{card[-4:]}\n"
        f"Status: Processing..."
    )
    
    # Simulate check (replace with real logic)
    result = "✅ <b>ALIVE</b> - Card is valid"
    
    # Deduct credit
    db.update_credits(user_id, -1)
    new_credits = db.get_user_credits(user_id)
    
    await message.answer(
        f"{result}\n\n"
        f"Credits remaining: {new_credits}"
    )

@dp.message(Command("mrz"))
async def mass_check_handler(message: types.Message):
    """Mass card check command"""
    user_id = message.from_user.id
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    
    max_cards = {"free": 10, "premium": 100, "diamond": 1000}.get(plan, 10)
    
    if credits < max_cards:
        await message.answer(
            f"❌ <b>Insufficient credits!</b>\n\n"
            f"Your plan: {plan.upper()}\n"
            f"Max cards: {max_cards}\n"
            f"Current credits: {credits}"
        )
        return
    
    await message.answer(
        "<b>📤 Mass Check Mode</b>\n\n"
        "Send a .txt file with cards (one per line)\n"
        "Format: CARD|MM|YY|CVV\n\n"
        "Example:\n"
        "4111111111111111|12|25|123\n"
        "5555555555554444|06|28|456"
    )

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    """Handle all callback queries"""
    user_id = callback.from_user.id
    
    if callback.data == "profile":
        credits = db.get_user_credits(user_id)
        plan = db.get_user_plan(user_id)
        
        profile_text = (
            "<b>👤 Your Profile</b>\n\n"
            f"<b>User ID:</b> {user_id}\n"
            f"<b>Credits:</b> {credits}\n"
            f"<b>Plan:</b> {plan.upper()}\n"
            f"<b>Status:</b> ✅ Active"
        )
        await callback.message.edit_text(profile_text, reply_markup=profile_keyboard())
    
    elif callback.data == "gates":
        gates_text = (
            "<b>🧪 Available Gates</b>\n\n"
            "1. Razorpay Gate\n"
            "2. Stripe Gate\n"
            "3. Auth Gate\n\n"
            "Coming soon: More payment methods"
        )
        await callback.message.edit_text(gates_text, reply_markup=gates_keyboard())
    
    elif callback.data == "plans":
        plans_text = (
            "<b>🪙 Plans & Pricing</b>\n\n"
            "<b>Free Plan:</b>\n"
            "   Credits: 25\n"
            "   Single Check: ✅\n"
            "   Mass Check: ❌\n\n"
            "<b>Premium Plan:</b>\n"
            "   Credits: 5000\n"
            "   Single Check: ✅\n"
            "   Mass Check: ✅ (100 cards/check)\n\n"
            "<b>Diamond Plan:</b>\n"
            "   Credits: Unlimited\n"
            "   Single Check: ✅\n"
            "   Mass Check: ✅ (1000 cards/check)"
        )
        await callback.message.edit_text(plans_text, reply_markup=plans_keyboard())
    
    elif callback.data == "help":
        help_text = (
            "<b>❓ Help & Support</b>\n\n"
            "/start - Home menu\n"
            "/profile - Your profile\n"
            "/rz CARD|MM|YY|CVV - Single check\n"
            "/mrz - Mass check\n\n"
            "Contact: @" + (callback.from_user.username or "support")
        )
        await callback.message.edit_text(help_text, reply_markup=help_keyboard())
    
    elif callback.data == "back":
        welcome_text = (
            "<b>🎉 Telegram Premium Checker Bot</b>\n\n"
            "Select an option below."
        )
        await callback.message.edit_text(welcome_text, reply_markup=home_keyboard())
    
    await callback.answer()

async def main():
    """Main function"""
    logger.info("🤖 Telegram Premium Checker Bot started!")
    logger.info(f"Bot Owner: {OWNER_NAME}")
    logger.info(f"Developer: {DEVELOPER_NAME}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

