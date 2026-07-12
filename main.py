#!/usr/bin/env python3
"""
Telegram Premium Checker Bot - Main Entry Point
Complete Production Ready Bot
"""

import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
import asyncio
import sys

from db import Database
from keyboards import home_keyboard, profile_keyboard, gates_keyboard, plans_keyboard, help_keyboard, back_button
from handlers.commands import help_handler, cmds_handler, stats_handler
from handlers.single_check import single_check_handler
from handlers.mass_check import mass_check_handler, process_mass_check_file
from handlers.navigation import profile_callback, gates_callback, plans_callback, help_callback, back_callback
from handlers.payment import payment_callback, razorpay_callback

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FSM States
class CheckState(StatesGroup):
    waiting_for_mass_file = State()

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
OWNER_NAME = os.getenv("OWNER_NAME", "Admin")
DEVELOPER_NAME = os.getenv("DEVELOPER_NAME", "Developer")

# Validate BOT_TOKEN
if not BOT_TOKEN:
    logger.critical("❌ BOT_TOKEN environment variable not set!")
    logger.critical("Please set BOT_TOKEN in Railway environment variables.")
    logger.critical("Get your bot token from @BotFather on Telegram.")
    sys.exit(1)

logger.info("✅ BOT_TOKEN loaded successfully")

# Initialize bot and dispatcher
bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML
)
dp = Dispatcher()
db = Database()

# ============= MESSAGE HANDLERS =============

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    """Start command handler"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "User"
    
    # Reset any ongoing state
    await state.clear()
    
    db.add_user(user_id, username, first_name)
    
    welcome_text = (
        f"🎉 <b>Welcome to Telegram Premium Checker Bot!</b>\n\n"
        f"👤 Hello <b>{first_name}</b>\n\n"
        f"Select an option below to get started.\n\n"
        f"<i>Bot Owner: {OWNER_NAME}</i>\n"
        f"<i>Developer: {DEVELOPER_NAME}</i>"
    )
    
    await message.answer(welcome_text, reply_markup=home_keyboard())

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    """Help command handler"""
    await help_handler(message)

@dp.message(Command("cmds"))
async def cmds_cmd(message: types.Message):
    """Commands list handler"""
    await cmds_handler(message)

@dp.message(Command("profile"))
async def profile_cmd(message: types.Message):
    """Profile command handler"""
    user_id = message.from_user.id
    credits = db.get_user_credits(user_id)
    plan = db.get_user_plan(user_id)
    stats = db.get_user_stats(user_id)
    
    profile_text = (
        "<b>👤 Your Profile</b>\n\n"
        f"<b>User ID:</b> {user_id}\n"
        f"<b>Username:</b> @{message.from_user.username or 'Unknown'}\n"
        f"<b>Name:</b> {message.from_user.first_name}\n"
        f"<b>Credits:</b> {credits}\n"
        f"<b>Plan:</b> {plan.upper()}\n"
        f"<b>Total Checks:</b> {stats['total_checks']}\n"
        f"<b>Alive Cards:</b> {stats['alive_checks']}\n"
        f"<b>Status:</b> ✅ Active"
    )
    
    await message.answer(profile_text, reply_markup=profile_keyboard())

@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):
    """Statistics command handler"""
    await stats_handler(message, db)

@dp.message(Command("rz"))
async def rz_cmd(message: types.Message, state: FSMContext):
    """Single card check command"""
    await single_check_handler(message, db)

@dp.message(Command("mrz"))
async def mrz_cmd(message: types.Message, state: FSMContext):
    """Mass card check command"""
    await mass_check_handler(message, db, state)

@dp.message()
async def message_handler(message: types.Message, state: FSMContext):
    """Handle all other messages"""
    current_state = await state.get_state()
    
    # If waiting for mass check file
    if current_state == CheckState.waiting_for_mass_file:
        await process_mass_check_file(message, db, state)
    else:
        await message.answer(
            "❌ <b>Unknown command</b>\n\n"
            "Use /help for available commands or /start to go home."
        )

# ============= CALLBACK HANDLERS =============

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handle all callback queries"""
    data = callback.data
    
    # Navigation callbacks
    if data == "profile":
        await profile_callback(callback, db)
    elif data == "gates":
        await gates_callback(callback)
    elif data == "plans":
        await plans_callback(callback)
    elif data == "help":
        await help_callback(callback)
    elif data == "back":
        await back_callback(callback)
    
    # Payment callbacks
    elif data.startswith("plan_"):
        await payment_callback(callback, db, state)
    elif data == "razorpay":
        await razorpay_callback(callback, db, state)
    
    else:
        await callback.answer(f"Unknown action: {data}", show_alert=True)

# ============= ERROR HANDLER =============

@dp.errors()
async def error_handler(update, exception):
    """Handle errors gracefully"""
    logger.error(f"Update error: {exception}", exc_info=True)

# ============= MAIN =============

async def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Premium Checker Bot starting...")
    logger.info("=" * 60)
    logger.info(f"Bot Owner: {OWNER_NAME}")
    logger.info(f"Developer: {DEVELOPER_NAME}")
    logger.info(f"Database: {db.db_path}")
    logger.info(f"Total users: {db.get_all_users_count()}")
    logger.info("=" * 60)
    logger.info("✅ Bot is READY. Listening for messages...")
    logger.info("=" * 60)
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot session closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted")
    except Exception as e:
        logger.critical(f"Startup error: {e}", exc_info=True)
        sys.exit(1)

