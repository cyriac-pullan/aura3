"""
AURA v3 - Telegram Bot Integration
Remote control AURA from your phone via Telegram.

Features:
- Send commands to AURA from Telegram and get responses back
- AURA can send messages, files, and photos TO you on Telegram
- Secure: only responds to your authorized chat ID
- Runs as a background thread alongside the main AURA widget

Setup:
1. Talk to @BotFather on Telegram → /newbot → get your BOT TOKEN
2. Send any message to your bot, then visit:
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   to find your chat_id
3. Add to .env:
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
"""

import os
import logging
import threading
import time
import asyncio
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("TelegramBot")

# Check availability
TELEGRAM_AVAILABLE = False
try:
    from telegram import Update, Bot
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("python-telegram-bot not installed. Run: pip install python-telegram-bot")


class TelegramManager:
    """
    Manages the Telegram bot for AURA remote control.
    
    Architecture:
    - Bot runs in a background thread with its own asyncio event loop
    - Incoming messages are routed through aura_v2_bridge.process_command()
    - Outbound messages use the bot's send_message/send_document/send_photo API
    """
    
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self._app = None          # telegram.ext.Application
        self._bot = None          # telegram.Bot (for outbound messages)
        self._thread = None       # Background polling thread
        self._loop = None         # Event loop for the background thread
        self._running = False
        self._bridge = None       # Lazy-loaded AURA bridge
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set in .env")
        if not self.chat_id:
            logger.warning("TELEGRAM_CHAT_ID not set in .env — bot will accept commands from anyone!")
    
    # ═══════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════
    
    def start(self) -> bool:
        """Start the Telegram bot in a background thread."""
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot not installed.")
            return False
        
        if not self.bot_token:
            logger.error("No TELEGRAM_BOT_TOKEN configured.")
            return False
        
        if self._running:
            logger.info("Telegram bot is already running.")
            return True
        
        self._running = True
        self._thread = threading.Thread(target=self._run_bot, daemon=True, name="TelegramBot")
        self._thread.start()
        logger.info("Telegram bot started in background thread.")
        return True
    
    def stop(self):
        """Stop the Telegram bot."""
        self._running = False
        if self._loop and self._app:
            # Schedule the application stop on its event loop
            try:
                asyncio.run_coroutine_threadsafe(self._app.stop(), self._loop)
            except Exception as e:
                logger.debug(f"Stop signal: {e}")
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        logger.info("Telegram bot stopped.")
    
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()
    
    # ═══════════════════════════════════════════════════════════════════
    # BACKGROUND BOT THREAD
    # ═══════════════════════════════════════════════════════════════════
    
    def _run_bot(self):
        """Runs the Telegram polling loop in a dedicated thread."""
        # Create a fresh event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._start_polling())
        except Exception as e:
            logger.error(f"Telegram bot thread error: {e}")
        finally:
            try:
                self._loop.close()
            except:
                pass
            self._running = False
    
    async def _start_polling(self):
        """Build and start the Telegram application."""
        self._app = ApplicationBuilder().token(self.bot_token).build()
        
        # Register handlers
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("status", self._cmd_status))
        self._app.add_handler(CommandHandler("stats", self._cmd_stats))
        self._app.add_handler(CommandHandler("clear", self._cmd_clear))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self._app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        self._app.add_handler(MessageHandler(filters.Document.ALL, self._handle_document))
        
        # Initialize and start
        await self._app.initialize()
        await self._app.start()
        
        # Store bot reference for outbound messages
        self._bot = self._app.bot
        
        logger.info("Telegram bot polling started. Waiting for messages...")
        
        # Start polling (this blocks until stopped)
        await self._app.updater.start_polling(drop_pending_updates=True)
        
        # Keep alive until stopped
        while self._running:
            await asyncio.sleep(1)
        
        # Cleanup
        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()
    
    # ═══════════════════════════════════════════════════════════════════
    # AUTHORIZATION
    # ═══════════════════════════════════════════════════════════════════
    
    def _is_authorized(self, update: Update) -> bool:
        """Check if the message sender is authorized."""
        if not self.chat_id:
            return True  # No restriction configured
        
        sender_id = str(update.effective_chat.id)
        return sender_id == str(self.chat_id)
    
    # ═══════════════════════════════════════════════════════════════════
    # AURA BRIDGE (lazy load)
    # ═══════════════════════════════════════════════════════════════════
    
    def _get_bridge(self):
        """Lazy-load the AURA bridge to avoid circular imports."""
        if self._bridge is None:
            try:
                from aura_v2_bridge import aura_bridge
                self._bridge = aura_bridge
            except ImportError as e:
                logger.error(f"Could not import AURA bridge: {e}")
        return self._bridge
    
    # ═══════════════════════════════════════════════════════════════════
    # COMMAND HANDLERS (/start, /help, /status, /stats, /clear)
    # ═══════════════════════════════════════════════════════════════════
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not self._is_authorized(update):
            await update.message.reply_text("⛔ Unauthorized. This bot is private.")
            return
        
        welcome = (
            "🤖 *AURA Remote Control*\n\n"
            "I'm your AI assistant, now accessible from Telegram!\n\n"
            "Just type any command like you would with voice:\n"
            "• `set volume to 50`\n"
            "• `open chrome`\n"
            "• `what's the weather today?`\n"
            "• `create a todo app`\n"
            "• `take a screenshot`\n\n"
            "Type /help for more options."
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not self._is_authorized(update):
            return
        
        help_text = (
            "📋 *AURA Commands*\n\n"
            "*System Control:*\n"
            "• `set volume to 50` / `mute`\n"
            "• `set brightness to 80`\n"
            "• `take a screenshot`\n"
            "• `system info` (battery, CPU, RAM)\n\n"
            "*Applications:*\n"
            "• `open chrome` / `close notepad`\n"
            "• `open file explorer`\n\n"
            "*Media:*\n"
            "• `play despacito on youtube`\n"
            "• `next track` / `pause`\n\n"
            "*Messaging:*\n"
            "• `send whatsapp to Alex saying hello`\n\n"
            "*AI-Powered:*\n"
            "• `create a calculator app`\n"
            "• `draft email to boss about leave`\n"
            "• Any question (conversation mode)\n\n"
            "*Bot Commands:*\n"
            "• /status — Check AURA status\n"
            "• /stats — Performance stats\n"
            "• /clear — Clear conversation history\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not self._is_authorized(update):
            return
        
        bridge = self._get_bridge()
        if bridge:
            status = (
                "✅ *AURA Status: Online*\n\n"
                f"🧠 Conversation history: {bridge.get_conversation_length()} messages\n"
                f"📡 Telegram bot: Running\n"
                f"🖥️ Platform: Windows"
            )
        else:
            status = "⚠️ *AURA Status: Bridge not loaded*"
        
        await update.message.reply_text(status, parse_mode="Markdown")
    
    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        if not self._is_authorized(update):
            return
        
        bridge = self._get_bridge()
        if bridge:
            stats = bridge.get_stats()
            stats_text = (
                "📊 *AURA Performance Stats*\n\n"
                f"⚡ Local commands: {stats.get('local_commands', 0)}\n"
                f"🔀 Multi-task: {stats.get('multi_task', 0)}\n"
                f"🎯 Goal-driven: {stats.get('goal_driven', 0)}\n"
                f"🤖 Gemini (intent): {stats.get('gemini_intent', 0)}\n"
                f"🤖 Gemini (full): {stats.get('gemini_full', 0)}\n"
                f"💬 Gemini (chat): {stats.get('gemini_chat', 0)}\n"
                f"💰 Tokens saved: ~{stats.get('tokens_saved', 0)}\n"
                f"📈 Total commands: {stats.get('total_commands', 0)}\n"
                f"📊 Local rate: {stats.get('local_percentage', 0):.1f}%"
            )
        else:
            stats_text = "⚠️ Stats not available — bridge not loaded."
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")
    
    async def _cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command — clears conversation history."""
        if not self._is_authorized(update):
            return
        
        bridge = self._get_bridge()
        if bridge:
            bridge.clear_conversation_history()
            await update.message.reply_text("🗑️ Conversation history cleared.")
        else:
            await update.message.reply_text("⚠️ Bridge not available.")
    
    # ═══════════════════════════════════════════════════════════════════
    # MESSAGE HANDLERS (main command processing)
    # ═══════════════════════════════════════════════════════════════════
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages — route through AURA."""
        if not self._is_authorized(update):
            await update.message.reply_text("⛔ Unauthorized.")
            return
        
        user_text = update.message.text.strip()
        if not user_text:
            return
        
        logger.info(f"Telegram command received: {user_text}")
        
        # Send "typing" indicator while processing
        await update.message.chat.send_action("typing")
        
        # Process through AURA bridge
        bridge = self._get_bridge()
        if not bridge:
            await update.message.reply_text("⚠️ AURA is not available right now.")
            return
        
        try:
            # Capture stdout during processing — many AURA functions print() 
            # their results (e.g. system_info prints "CPU: 0.0%, RAM: 81.6%")
            # but bridge.process() only returns a generic confirmation.
            import io, sys
            
            def _process_with_capture():
                old_stdout = sys.stdout
                sys.stdout = captured = io.StringIO()
                try:
                    response, success, used_gemini = bridge.process(user_text)
                finally:
                    sys.stdout = old_stdout
                captured_output = captured.getvalue().strip()
                return response, success, used_gemini, captured_output
            
            # Run in thread pool to avoid blocking the event loop
            response, success, used_gemini, captured_output = await asyncio.get_event_loop().run_in_executor(
                None, _process_with_capture
            )
            
            # Build rich reply combining response + captured output
            if success:
                emoji = "🤖" if used_gemini else "⚡"
                
                # If the response is a generic confirmation but we have real data
                # from stdout, show the data instead
                generic_confirmations = [
                    "done", "certainly", "right away", "as you wish",
                    "of course", "straightaway", "at once", "consider it done",
                    "very well", "executed", "completed"
                ]
                response_is_generic = any(
                    g in response.lower() for g in generic_confirmations
                ) and len(response) < 80
                
                if captured_output and response_is_generic:
                    # Use captured output as the primary response
                    reply = f"{emoji} {captured_output}"
                elif captured_output and captured_output not in response:
                    # Append captured output to the response
                    reply = f"{emoji} {response}\n\n📋 {captured_output}"
                else:
                    reply = f"{emoji} {response}"
            else:
                reply = f"❌ {response}" if response else "❌ Command failed."
                if captured_output:
                    reply += f"\n\n📋 {captured_output}"
            
            # Telegram has a 4096 char limit per message
            if len(reply) > 4000:
                # Split into chunks
                for i in range(0, len(reply), 4000):
                    chunk = reply[i:i + 4000]
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(reply)
                
        except Exception as e:
            logger.error(f"Error processing Telegram command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")
    
    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming photos with optional caption as command."""
        if not self._is_authorized(update):
            return
        
        caption = update.message.caption or ""
        await update.message.reply_text(
            f"📸 Photo received! Caption: '{caption}'\n"
            "Photo analysis coming soon (Gemini Vision integration)."
        )
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming documents/files."""
        if not self._is_authorized(update):
            return
        
        doc = update.message.document
        await update.message.reply_text(
            f"📎 File received: `{doc.file_name}` ({doc.file_size} bytes)\n"
            "File processing coming soon.",
            parse_mode="Markdown"
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # OUTBOUND METHODS (AURA → Telegram)
    # ═══════════════════════════════════════════════════════════════════
    
    def send_message(self, text: str, chat_id: str = None) -> bool:
        """
        Send a text message to the user on Telegram.
        
        Args:
            text: Message text to send
            chat_id: Target chat ID (defaults to configured TELEGRAM_CHAT_ID)
        
        Returns:
            True if message was sent successfully
        """
        target = chat_id or self.chat_id
        if not target:
            logger.error("No chat_id specified and TELEGRAM_CHAT_ID not configured.")
            return False
        
        if not self._bot and not self._running:
            # Bot not running, try to send via direct API call
            return self._send_direct(target, text)
        
        if not self._loop or not self._bot:
            logger.error("Bot not initialized. Call start() first.")
            return False
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._bot.send_message(chat_id=int(target), text=text),
                self._loop
            )
            future.result(timeout=10)  # Wait up to 10 seconds
            logger.info(f"Telegram message sent to {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_file(self, file_path: str, caption: str = "", chat_id: str = None) -> bool:
        """
        Send a file to the user on Telegram.
        
        Args:
            file_path: Path to the file to send
            caption: Optional caption for the file
            chat_id: Target chat ID
        
        Returns:
            True if sent successfully
        """
        target = chat_id or self.chat_id
        if not target:
            logger.error("No chat_id configured.")
            return False
        
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        if not self._loop or not self._bot:
            logger.error("Bot not initialized. Call start() first.")
            return False
        
        try:
            async def _send():
                with open(path, 'rb') as f:
                    await self._bot.send_document(
                        chat_id=int(target),
                        document=f,
                        caption=caption or path.name
                    )
            
            future = asyncio.run_coroutine_threadsafe(_send(), self._loop)
            future.result(timeout=30)
            logger.info(f"File sent via Telegram: {path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send file via Telegram: {e}")
            return False
    
    def send_photo(self, photo_path: str, caption: str = "", chat_id: str = None) -> bool:
        """
        Send a photo/image to the user on Telegram.
        
        Args:
            photo_path: Path to the image file
            caption: Optional caption
            chat_id: Target chat ID
        
        Returns:
            True if sent successfully
        """
        target = chat_id or self.chat_id
        if not target:
            logger.error("No chat_id configured.")
            return False
        
        path = Path(photo_path)
        if not path.exists():
            logger.error(f"Photo not found: {photo_path}")
            return False
        
        if not self._loop or not self._bot:
            logger.error("Bot not initialized. Call start() first.")
            return False
        
        try:
            async def _send():
                with open(path, 'rb') as f:
                    await self._bot.send_photo(
                        chat_id=int(target),
                        photo=f,
                        caption=caption
                    )
            
            future = asyncio.run_coroutine_threadsafe(_send(), self._loop)
            future.result(timeout=30)
            logger.info(f"Photo sent via Telegram: {path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send photo via Telegram: {e}")
            return False
    
    def _send_direct(self, chat_id: str, text: str) -> bool:
        """Send a message using direct HTTP API (when bot is not running)."""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Direct Telegram API call failed: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE & CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_telegram_manager = None


def get_telegram_manager() -> TelegramManager:
    """Get or create the global TelegramManager instance."""
    global _telegram_manager
    if _telegram_manager is None:
        _telegram_manager = TelegramManager()
    return _telegram_manager


def start_telegram_bot() -> bool:
    """Start the Telegram bot. Returns True if started successfully."""
    mgr = get_telegram_manager()
    return mgr.start()


def stop_telegram_bot():
    """Stop the Telegram bot."""
    mgr = get_telegram_manager()
    mgr.stop()


def send_telegram_message(text: str) -> bool:
    """Send a message to the configured Telegram chat."""
    mgr = get_telegram_manager()
    return mgr.send_message(text)


def send_telegram_file(file_path: str, caption: str = "") -> bool:
    """Send a file to the configured Telegram chat."""
    mgr = get_telegram_manager()
    return mgr.send_file(file_path, caption)


def send_telegram_photo(photo_path: str, caption: str = "") -> bool:
    """Send a photo to the configured Telegram chat."""
    mgr = get_telegram_manager()
    return mgr.send_photo(photo_path, caption)


def is_available() -> bool:
    """Check if Telegram bot is available (package installed + token configured)."""
    return TELEGRAM_AVAILABLE and bool(os.environ.get("TELEGRAM_BOT_TOKEN"))


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if not is_available():
        print("Telegram bot not available.")
        print(f"  - python-telegram-bot installed: {TELEGRAM_AVAILABLE}")
        print(f"  - TELEGRAM_BOT_TOKEN set: {bool(os.environ.get('TELEGRAM_BOT_TOKEN'))}")
        print(f"  - TELEGRAM_CHAT_ID set: {bool(os.environ.get('TELEGRAM_CHAT_ID'))}")
        print("\nTo set up:")
        print("1. pip install python-telegram-bot")
        print("2. Talk to @BotFather on Telegram to create a bot")
        print("3. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to your .env file")
    else:
        print("Starting Telegram bot... Press Ctrl+C to stop.")
        mgr = get_telegram_manager()
        mgr.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            mgr.stop()
            print("Done.")
