import traceback
import discord
import os
import asyncio
import logging
from dotenv import load_dotenv
from bot import get_bot, set_error_notifier  # Updated import
from core.sync import load_cogs

# Import custom logging modules
from logger.logger_setup import setup_application_logging, EmailErrorHandler
from logger.log_dispacher import EnhancedErrorNotifier, Severity, ErrorCategory

# Import database manager
from database import db_core, guild_manager, ensure_database_connection

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("PASSWORD")  # This should be an App Password for Gmail
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")  # Added for database configuration

# Ensure log directory exists
LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

# --- Setup Logging ---
# Initialize the main application logger
app_logger = setup_application_logging(
    app_name="DiscordBot",
    log_level=logging.INFO,
    log_dir=LOG_DIR,
    enable_performance_logging=True
)

# Get the bot instance
bot = get_bot()

# Initialize the EnhancedErrorNotifier
error_notifier = None
if EMAIL_ADDRESS and EMAIL_PASSWORD:
    error_notifier = EnhancedErrorNotifier(
        email=EMAIL_ADDRESS,
        app_password=EMAIL_PASSWORD,
        bot_instance=bot,  # Pass the bot instance
        interval=300,  # Send error reports every 5 minutes
        enable_html=True,
        enable_attachments=True,
        severity_threshold=Severity.LOW  # Report all errors
    )
    # Set the error notifier in bot.py so it can access it
    set_error_notifier(error_notifier)

    # Import the utility function
    from logger.logger_setup import add_global_handler

    # Add email handler to all loggers (existing and future)
    email_handler = EmailErrorHandler(error_notifier)
    add_global_handler(email_handler)

    app_logger.info("Email error notification enabled.")
else:
    # Set None in bot.py as well
    set_error_notifier(None)
    app_logger.warning("EMAIL or PASSWORD not set in .env. Email error notification disabled.")


async def initialize_database():
    """Initialize the database connection and setup."""
    try:
        app_logger.info("Initializing database connection...")

        # Initialize database core
        success = await db_core.initialize()
        if not success:
            app_logger.error("Failed to initialize database connection")
            return False

        # Initialize default bot settings
        await guild_manager.initialize_default_settings()

        app_logger.info("✅ Database initialization completed successfully")
        return True

    except Exception as e:
        app_logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        return False


async def shutdown_database():
    """Cleanly shutdown database connections."""
    try:
        app_logger.info("Shutting down database connections...")
        await db_core.close()
        app_logger.info("✅ Database connections closed")
    except Exception as e:
        app_logger.error(f"❌ Error during database shutdown: {e}")


async def main():
    # --- Initialize Database First ---
    db_initialized = await initialize_database()
    if not db_initialized:
        app_logger.critical("Database initialization failed. Bot cannot start without database.")
        return

    # --- Run the Bot ---
    if not DISCORD_TOKEN:
        app_logger.critical("DISCORD_TOKEN not found in .env file. Please set it to run the bot.")
        print("Error: DISCORD_TOKEN not found. Please set it in the .env file.")
        return

    try:
        app_logger.info("Starting Discord bot...")

        # Start the error notification loop AFTER the event loop is running
        if error_notifier:
            asyncio.create_task(error_notifier.start_loop(bot))
            app_logger.info("Error notification loop started.")

        # Load cogs (extensions)
        await load_cogs()
        app_logger.info("Cogs loaded successfully")

        # Start the bot
        app_logger.info("Connecting to Discord...")
        await bot.start(DISCORD_TOKEN)

    except discord.LoginFailure:
        app_logger.critical("Failed to log in to Discord. Check your DISCORD_TOKEN.")
        print("Error: Failed to log in. Check your DISCORD_TOKEN.")
    except discord.PrivilegedIntentsRequired:
        app_logger.critical("Privileged intents required. Enable them in the Discord Developer Portal.")
        print("Error: Privileged intents required. Enable them in the Discord Developer Portal.")
    except KeyboardInterrupt:
        app_logger.info("Bot shutdown requested by user (Ctrl+C)")
    except Exception as e:
        app_logger.critical(f"An unexpected error occurred during bot startup: {e}", exc_info=True)
        print(f"Error during bot startup: {e}")
        traceback.print_exc()
    finally:
        # Ensure clean shutdown
        await shutdown_bot()


async def shutdown_bot():
    """Cleanly shutdown the bot and all services."""
    app_logger.info("Initiating bot shutdown...")

    try:
        # Close bot connection
        if not bot.is_closed():
            await bot.close()
            app_logger.info("✅ Discord connection closed")

        # Shutdown database
        await shutdown_database()

        # Shutdown error notifier
        if error_notifier:
            try:
                await error_notifier.shutdown()
                app_logger.info("✅ Error notifier shut down")
            except Exception as e:
                app_logger.error(f"Error shutting down error notifier: {e}")

        app_logger.info("👋 Bot shutdown completed successfully")

    except Exception as e:
        app_logger.error(f"❌ Error during bot shutdown: {e}", exc_info=True)


def handle_exception(loop, context):
    """Handle exceptions from the event loop."""
    exception = context.get('exception')
    if exception:
        app_logger.critical(f"Unhandled exception in event loop: {exception}", exc_info=True)

        # Notify error notifier if available
        if error_notifier:
            asyncio.create_task(
                error_notifier.notify_error(
                    "Event Loop Error",
                    str(exception),
                    "Event Loop"
                )
            )
    else:
        app_logger.error(f"Event loop error: {context['message']}")


if __name__ == '__main__':
    # Set up exception handling for the event loop
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

    try:
        # Run the main function
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        app_logger.info("Bot shutdown requested by user (Ctrl+C)")
    except Exception as e:
        app_logger.critical(f"Fatal error in main: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        traceback.print_exc()
    finally:
        # Ensure clean shutdown even if main fails
        if not loop.is_closed():
            loop.run_until_complete(shutdown_bot())
            loop.close()
        app_logger.info("Application terminated")

# Instructions for the user:
# 1. Install required libraries: pip install discord.py python-dotenv
# 2. Create a Discord bot application on the Discord Developer Portal.
# 3. Get your bot's token and add it to the .env file as DISCORD_TOKEN.
# 4. If you want email notifications, set EMAIL and PASSWORD (Gmail App Password) in .env.
# 5. Run this script: python main.py