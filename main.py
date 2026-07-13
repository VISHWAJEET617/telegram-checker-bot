#!/usr/bin/env python3
"""Telegram Card Checker Bot - Main Entry Point"""

import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from handlers.single_check import single_check_handler
from handlers.batch_check import batch_check_start, batch_card_handler, BatchCheckState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init Bot & Dispatcher
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Database
from database import Database
db = Database()

# ============================================
# COMMAND HANDLERS
# ============================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Start command"""
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    balance = db.get_user_balance(user_id)
    
    await message.answer(f"""
💎 Welcome {username}!

📊 Your Balance: ₹{balance/100:.2f}

🎯 Commands:
/rz CARD|MM|YY|CVV  - Check single card
/mrz                - Batch check mode

Example:
/rz 5306908108485578|02|30|407

Only ALIVE cards charge ₹10
DECLINED/ERROR cards are FREE
""")

@dp.message(Command("rz"))
async def rz_handler(message: types.Message):
    """Single card check command"""
    await single_check_handler(message, db)

@dp.message(Command("mrz"))
async def mrz_handler(message: types.Message, state: FSMContext):
    """Batch check command"""
    await batch_check_start(message, state, db)

# ============================================
# MESSAGE HANDLERS
# ============================================

@dp.message()
async def message_handler(message: types.Message, state: FSMContext):
    """Handle messages in batch mode"""
    current_state = await state.get_state()
    
    # Only handle if in batch check state
    if current_state == BatchCheckState.waiting_for_cards.state:
        await batch_card_handler(message, state, db)
    else:
        await message.answer("""
Use /rz or /mrz to start checking cards

/rz CARD|MM|YY|CVV  - Single card
/mrz                - Batch mode
""")

# ============================================
# STARTUP
# ============================================

async def main():
    logger.info("🚀 Bot starting...")
    logger.info(f"Bot token: {os.getenv('BOT_TOKEN')[:10]}...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

