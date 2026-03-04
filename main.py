import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(router)
    
    # Start polling
    try:
        print("Starting bot...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("Bot stopped by user")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())