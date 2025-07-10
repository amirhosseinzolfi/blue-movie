import logging
import random
import os
import asyncio
import threading
import socket
import time  # For timeouts and performance measurements
import json  # <-- Add for JSON database
from http.server import HTTPServer, SimpleHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token - consider using environment variables for sensitive data
# import os
# TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TOKEN = "7883923399:AAHA0YDc4GSznty5bmDbxYikFefIJdnwjDI"

# Predefined channels list
ALL_CHANNELS = ["@channelA", "@channelB", "@channelC", "@channelD", "@channelE", "@channelF", "@channelG"]

# Global dict for storing user-specific recommended channels
user_channels = {}

# Static file server config
SERVER_HOST = "141.98.210.149"
SERVER_PORT = 8004  # Changed from 800 to 8004

# Button Texts
SEARCH_BUTTON_TEXT = "جستجوی فیلم 🔎"
BEST_MOVIES_BUTTON_TEXT = "250 فیلم برتر 🏆"

# Path to the movies database JSON file
MOVIE_DB_PATH = os.path.join(os.path.dirname(__file__), "movie_database.json")

def load_movies_db():
    """Load movies database from JSON file."""
    try:
        with open(MOVIE_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load movie database: {e}")
        return {}

def save_movies_db(movies):
    """Save movies database to JSON file."""
    try:
        with open(MOVIE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save movie database: {e}")

# Load movies at startup
MOVIES = load_movies_db()

# Channel configuration
FIXED_CHANNEL_URL = "https://t.me/Alltelegramproxy0"
FIXED_CHANNEL_USERNAME = "@Alltelegramproxy0"

# Conversation states
SEARCH = 1

# Helper function to send the main menu with ReplyKeyboardMarkup
async def send_main_menu(chat_id: int, context: CallbackContext, message_text: str):
    keyboard_buttons = [
        [SEARCH_BUTTON_TEXT, BEST_MOVIES_BUTTON_TEXT],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_buttons, resize_keyboard=True, one_time_keyboard=False) # Persistent
    await context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)

# Command handlers
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    # Handle deep-linking with /start movie_XXX
    args = context.args if hasattr(context, "args") else []
    if args and args[0].startswith("movie_"):
        movie_id = args[0].replace("movie_", "")
        movie_info = get_movie_by_id(movie_id)
        if movie_info:
            # Generate proper download URL for locally stored movies
            download_url = movie_info['download_link']
            if movie_info['url'].startswith('/root/blue_movie/movies/'):
                file_name = os.path.basename(movie_info['url'])
                timestamp = int(time.time())
                server_download_url = f"http://{SERVER_HOST}:{SERVER_PORT}/{file_name}?t={timestamp}"
                download_url = server_download_url

            detailed_info = f"""
🎬 **{movie_info['title']}** ({movie_info['year']})

📖 **خلاصه داستان:**
{movie_info['description']}



🎭 **ژانر:** {movie_info['genre']}
🎬 **کارگردان:** {movie_info['director']}
👥 **بازیگران اصلی:** {movie_info['cast']}
⏱️ **مدت زمان:** {movie_info['duration']}
📱 **کیفیت موجود:** {movie_info['quality']}
• **زبان:** {movie_info['language']}
• **زیرنویس:** فارسی

⭐️ **امتیاز IMDB:** {movie_info['imdb']}/10
            """
            download_keyboard = [[
                InlineKeyboardButton("📥 دانلود فایل", url=download_url)
            ]]
            # Send movie cover as photo with caption
            image_path = movie_info.get('image', '')
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as photo_file:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=detailed_info,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(download_keyboard)
                    )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=detailed_info,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(download_keyboard)
                )
            return  # Do not show main menu, just send the movie card
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ اطلاعات فیلم یافت نشد!")
            return

    # Ensure user_channels is initialized for the user
    if chat_id not in user_channels:
        user_channels[chat_id] = [FIXED_CHANNEL_USERNAME]

    if await is_subscribed(chat_id, context):
        await send_main_menu(chat_id, context, "به منوی اصلی خوش آمدید! گزینه خود را انتخاب کنید:")
    else:
        text = "✨ سلام دوست مهربان! 🌹\nبرای لذت بردن از فیلم‌های ویژه، ابتدا در کانال زیر عضو شوید:\n👉 " + FIXED_CHANNEL_USERNAME
        keyboard = [
            [InlineKeyboardButton(f"📣 {FIXED_CHANNEL_USERNAME}", url=FIXED_CHANNEL_URL)],
            [InlineKeyboardButton("✅ عضو شدم", callback_data="check_channels")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)

async def check_channels(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id
    
    # Ensure user_channels is initialized (it should be by `start`, but as a fallback)
    if chat_id not in user_channels:
        user_channels[chat_id] = [FIXED_CHANNEL_USERNAME]
        
    recommended = user_channels.get(chat_id, [])
    not_joined = []

    # Check membership status for each recommended channel
    for channel in recommended:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=chat_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel)
        except Exception as e:
            if "inaccessible" in str(e).lower():
                # Assume joined if the member list is inaccessible
                logger.info(f"Assuming membership for {channel} due to inaccessible error")
            else:
                logger.error(f"Error checking membership for {channel}: {e}")
                not_joined.append(channel)

    if not_joined:
        alert_text = "😢⚠️ ابتدا باید در کانال عضو شوید تا از فیلم‌های جذاب بهره ببرید! 🙏"
        keyboard = [
            [InlineKeyboardButton(f"📣 {FIXED_CHANNEL_USERNAME}", url=FIXED_CHANNEL_URL)],
            [InlineKeyboardButton("✅ عضو شدم", callback_data="check_channels")]
        ]
        try:
            await query.edit_message_text(text=alert_text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Edit message error: {e}")
        await query.answer(text=alert_text, show_alert=True)
    else:
        await query.answer(text="🎊 عالی! عضویت شما تایید شد.", show_alert=True)
        try:
            await query.delete_message() # Delete the "عضو شدم" inline keyboard message
        except Exception as e:
            logger.warning(f"Could not delete original message after channel check: {e}")
        
        await send_main_menu(chat_id, context, "🎊 عضویت شما تایید شد!\nاکنون از امکانات ربات استفاده کنید:")

async def is_subscribed(chat_id, context: CallbackContext):
    # Ensure user_channels has a default for the chat_id if not present
    recommended = user_channels.get(chat_id)
    if recommended is None:
        logger.warning(f"user_channels not found for {chat_id} in is_subscribed. Defaulting to FIXED_CHANNEL.")
        user_channels[chat_id] = [FIXED_CHANNEL_USERNAME]
        recommended = user_channels[chat_id]
        
    not_joined = []

    # Check membership status for each recommended channel
    for channel in recommended:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=chat_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel)
        except Exception as e:
            if "inaccessible" in str(e).lower():
                # Assume joined if the member list is inaccessible
                logger.info(f"Assuming membership for {channel} due to inaccessible error")
            else:
                logger.error(f"Error checking membership for {channel}: {e}")
                not_joined.append(channel)

    return not not_joined

async def search_start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    # Ensure user_channels is initialized for robustness
    if chat_id not in user_channels:
        user_channels[chat_id] = [FIXED_CHANNEL_USERNAME]

    if not await is_subscribed(chat_id, context):
        alert_text = "⚠️ لطفاً ابتدا در کانال عضو شوید تا بتوانید از امکانات جستجو استفاده کنید!"
        await update.message.reply_text(alert_text)
        return ConversationHandler.END
    
    await update.message.reply_text("🔍 لطفاً کلمه جستجو را وارد کنید:")
    return SEARCH

# Helper function to get movie by ID
def get_movie_by_id(movie_id: str):
    return MOVIES.get(movie_id)

# Helper function to search movies by title
def search_movies_by_title(query: str):
    results = {}
    for movie_id, movie_info in MOVIES.items():
        if query.lower() in movie_info['title'].lower():
            results[movie_id] = movie_info
    return results

async def search_received(update: Update, context: CallbackContext):
    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text("❌ لطفاً کلمه جستجو را وارد کنید. مثال: داستان")
        return SEARCH
    
    results = search_movies_by_title(query_text)
    
    if not results:
        await update.message.reply_text("❌ فیلمی مطابق با جستجو یافت نشد!")
    else:
        keyboard = [[InlineKeyboardButton(f"🎬 {movie_info['title']}", callback_data=f"movie_{movie_id}")]
                    for movie_id, movie_info in results.items()]

        response_text = ("🎬 نتایج جستجو:\n"
                         "برای مشاهده جزئیات و پیش‌نمایش، روی دکمه مربوطه کلیک کنید.\n"
                         "⏳ (توجه: پیش‌نمایش به مدت 10 ثانیه نمایش داده می‌شود)")
        await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def best_movies(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    # Ensure user_channels is initialized for robustness
    if chat_id not in user_channels:
        user_channels[chat_id] = [FIXED_CHANNEL_USERNAME]

    if not await is_subscribed(chat_id, context):
        alert_text = "⚠️ لطفاً ابتدا در کانال عضو شوید تا بتوانید از امکانات مشاهده بهترین‌ها استفاده کنید!"
        await update.message.reply_text(alert_text)
        return
    
    sorted_movies = sorted(MOVIES.items(), key=lambda x: float(x[1]['imdb']), reverse=True)[:10]
    keyboard = [[InlineKeyboardButton(f"🎬 {movie_info['title']} ({movie_info['imdb']})", callback_data=f"movie_{movie_id}")]
                for movie_id, movie_info in sorted_movies]
    response_text = ("🎖 بهترین‌های تاریخ (10 فیلم برتر):\n"
                     "برای مشاهده جزئیات و پیش‌نمایش، روی دکمه مربوطه کلیک کنید.\n"
                     "⏳ (توجه: پیش‌نمایش به مدت 10 ثانیه نمایش داده می‌شود)")
    await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def movie_preview(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    movie_id = query.data.split("_", 1)[1]
    movie_info = get_movie_by_id(movie_id)
    
    if movie_info:
        movie_title = movie_info['title']
        notify_msg = await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"🎥 در حال آماده‌سازی اطلاعات «{movie_title}»..."
        )
        
        # Generate proper download URL for locally stored movies
        download_url = movie_info['download_link']
        if movie_info['url'].startswith('/root/blue_movie/movies/'):
            file_name = os.path.basename(movie_info['url'])
            timestamp = int(time.time())
            server_download_url = f"http://{SERVER_HOST}:{SERVER_PORT}/{file_name}?t={timestamp}"
            download_url = server_download_url
        
        detailed_info = f"""
🎬 **{movie_info['title']}** ({movie_info['year']})

📖 **خلاصه داستان:**
{movie_info['description']}



🎭 **ژانر:** {movie_info['genre']}
🎬 **کارگردان:** {movie_info['director']}
👥 **بازیگران اصلی:** {movie_info['cast']}
⏱️ **مدت زمان:** {movie_info['duration']}
📱 **کیفیت موجود:** {movie_info['quality']}
• **زبان:** {movie_info['language']}
• **زیرنویس:** فارسی

⭐️ **امتیاز IMDB:** {movie_info['imdb']}/10
        """
        download_keyboard = [[
            InlineKeyboardButton("📥 دانلود فایل", url=download_url)
        ]]
        # Send movie cover as photo with caption
        image_path = movie_info.get('image', '')
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as photo_file:
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=photo_file,
                    caption=detailed_info,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(download_keyboard)
                )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=detailed_info,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(download_keyboard)
            )
        logger.info(f"Download link generated for {movie_title}: {download_url}")
        try:
            await context.bot.delete_message(chat_id=query.message.chat.id, message_id=notify_msg.message_id)
        except Exception:
            pass
    else:
        await context.bot.send_message(chat_id=query.message.chat.id, text="❌ اطلاعات فیلم یافت نشد!")

async def set_commands(app: Application):
    commands = [
        BotCommand("start", "شروع ربات و دریافت دستورات"),
        BotCommand("search", "جستجوی فیلم (مثال: /search داستان)"),
        BotCommand("bestmovies", "نمایش بهترین فیلم‌ها بر اساس امتیاز IMDB")
    ]
    try:
        # Fix CommandScope import - it should be imported from telegram, not telegram.ext
        from telegram import BotCommandScopeDefault
        await app.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info("Bot commands have been set successfully")
    except Exception as e:
        logger.error(f"Error setting bot commands: {e}")

def main():
    application = Application.builder().token(TOKEN).post_init(set_commands).build()
    
    # Add conversation handler for /search command and search button
    search_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_start),
            MessageHandler(filters.TEXT & filters.Regex(f"^{SEARCH_BUTTON_TEXT}$"), search_start)
        ],
        states={
            SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_received)]
        },
        fallbacks=[]
    )
    
    application.add_handler(search_conv_handler)
    
    # Handler for best movies command and button
    application.add_handler(CommandHandler("bestmovies", best_movies))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"^{BEST_MOVIES_BUTTON_TEXT}$"), best_movies))
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_channels, pattern='^check_channels$'))
    application.add_handler(CallbackQueryHandler(movie_preview, pattern='^movie_'))
    
    application.run_polling()

def start_file_server():
    # serve files from the 'movies' subfolder, bind to all interfaces
    movies_dir = os.path.join(os.path.dirname(__file__), "movies")
    if os.path.exists(movies_dir):
        os.chdir(movies_dir)
        class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
            # Set a large buffer size (16 MB) for faster file transfers
            rbufsize = 16 * 1024 * 1024  # Read buffer size
            wbufsize = 16 * 1024 * 1024  # Write buffer size
            
            # Override to handle broken pipe and other connection errors gracefully
            def handle_one_request(self):
                try:
                    return SimpleHTTPRequestHandler.handle_one_request(self)
                except BrokenPipeError:
                    # Client disconnected during download - this is normal behavior
                    logger.debug("Client disconnected during file download")
                except ConnectionResetError:
                    # Client closed connection
                    logger.debug("Connection reset by client")
                except Exception as e:
                    logger.error(f"Error serving file: {e}")
            
            def guess_type(self, path):
                # Always return application/octet-stream for video files to force download
                if path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')):
                    return 'application/octet-stream', None
                mimetype, encoding = super().guess_type(path)
                return mimetype, encoding
            
            def copyfile(self, source, outputfile):
                """Copy data from source to outputfile in larger chunks for better performance"""
                CHUNK_SIZE = 64 * 1024 * 1024  # 64 MB chunks for faster transfer
                while True:
                    buf = source.read(CHUNK_SIZE)
                    if not buf:
                        break
                    outputfile.write(buf)

            def translate_path(self, path):
                """Override to ensure proper handling of non-ASCII filenames"""
                path = super().translate_path(path)
                return path

            def send_head(self):
                """Common code for GET and HEAD commands.
                Override to handle large files more efficiently.
                """
                path = self.translate_path(self.path)
                if os.path.isdir(path):
                    return super().send_head()
                
                # Handle non-directory requests - mainly file downloads
                try:
                    f = open(path, 'rb')
                except OSError:
                    self.send_error(404, "File not found")
                    return None
                
                try:
                    fs = os.fstat(f.fileno())
                    content_type = self.guess_type(path)[0] or 'application/octet-stream'
                    self.send_response(200)
                    self.send_header("Content-type", content_type)
                    self.send_header("Content-Length", str(fs[6]))
                    self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                    
                    # Always force file download with Content-Disposition header
                    filename = os.path.basename(path)
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    
                    # Optimization headers
                    self.send_header('Accept-Ranges', 'bytes')
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.send_header('Content-Transfer-Encoding', 'binary')
                    
                    self.end_headers()
                    return f
                except:
                    f.close()
                    raise
                    
            def log_message(self, format, *args):
                # More concise logging for file server
                if args[1] == "200":  # Only log successful requests at info level
                    logger.info(f"Serving file: {args[0]} - Status {args[1]}")
                else:
                    logger.warning(f"File server: {format % args}")

        # Use ThreadingHTTPServer for concurrent downloads
        try:
            from http.server import ThreadingHTTPServer
        except ImportError:
            # Python <3.7 fallback
            from socketserver import ThreadingMixIn
            class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
                daemon_threads = True

        httpd = ThreadingHTTPServer(("0.0.0.0", SERVER_PORT), CustomHTTPRequestHandler)
        httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # Set TCP keep-alive parameters if on Linux
        try:
            # TCP_KEEPIDLE: time before sending keepalive probes
            httpd.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            # TCP_KEEPINTVL: time between keepalive probes
            httpd.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            # TCP_KEEPCNT: number of keepalive probes
            httpd.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
        except (AttributeError, OSError):
            # These options might not be available on all platforms
            pass
            
        logger.info(f"Optimized file server started on http://0.0.0.0:{SERVER_PORT}")
        httpd.serve_forever()
    else:
        logger.warning(f"Movies directory not found: {movies_dir}")

# launch file server in background
threading.Thread(target=start_file_server, daemon=True).start()

if __name__ == '__main__': 
    main()