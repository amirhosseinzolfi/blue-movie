import logging
import random
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, MessageHandler, filters

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

# Button Texts
SEARCH_BUTTON_TEXT = "جستجوی فیلم 🔎"
BEST_MOVIES_BUTTON_TEXT = "250 فیلم برتر 🏆"

# Movies available with preview video URL
MOVIES = {
    "The Shawshank Redemption": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "9.3",
        "description": "داستان دوستی و امید در زندان شاوشنک، قوی‌ترین نیروی جهان"
    },
    "The Godfather": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "9.2",
        "description": "حماسه خانواده کورلئونه و داستان مافیای ایتالیایی آمریکایی"
    },
    "The Dark Knight": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "9.0",
        "description": "مبارزه بتمن با جوکر، آشوبگر روانی که گاتهام را به هرج و مرج می‌کشد"
    },
    "Pulp Fiction": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.9",
        "description": "داستان‌های به هم پیچیده گانگسترها، بوکسور، و دزدان در لس‌آنجلس"
    },
    "Fight Club": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.8",
        "description": "مردی بی‌خواب با شخصیت کاریزماتیک تایلر داردن یک باشگاه مبارزه زیرزمینی تشکیل می‌دهد"
    },
    "Inception": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.8",
        "description": "دزدی از رویاها و کاشتن ایده در ذهن ناخودآگاه افراد در لایه‌های مختلف خواب"
    },
    "The Matrix": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.7",
        "description": "هکری که متوجه می‌شود دنیا یک شبیه‌سازی کامپیوتری است و به مبارزه با ماشین‌ها می‌پردازد"
    },
    "Interstellar": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.6",
        "description": "سفری حماسی به اعماق فضا برای یافتن سیاره‌ای قابل سکونت برای نجات بشریت"
    },
    "Parasite": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.5",
        "description": "داستان خانواده‌ای فقیر که به صورت انگل وارد زندگی خانواده‌ای ثروتمند می‌شوند"
    },
    "Joker": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.4",
        "description": "روایتی تاریک از شکل‌گیری شخصیت جوکر و تبدیل یک کمدین شکست‌خورده به تبهکار"
    },
    "Spider-Man: Into the Spider-Verse": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.4",
        "description": "مایلز مورالس با مرد عنکبوتی‌های دنیاهای موازی همکاری می‌کند تا دنیا را نجات دهند"
    },
    "Avengers: Endgame": {
        "url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "imdb": "8.4",
        "description": "انتقام‌جویان تلاش می‌کنند تا اقدامات مخرب تانوس را خنثی کنند"
    }
}

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

async def search_received(update: Update, context: CallbackContext):
    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text("❌ لطفاً کلمه جستجو را وارد کنید. مثال: داستان")
        return SEARCH
    results = {}
    for title, info in MOVIES.items():
        if query_text.lower() in title.lower():
            results[title] = info
    if not results:
        await update.message.reply_text("❌ فیلمی مطابق با جستجو یافت نشد!")
    else:
        keyboard = [[InlineKeyboardButton(f"🎬 {title}", callback_data=f"movie_{title}")]
                    for title in results.keys()]

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
    keyboard = [[InlineKeyboardButton(f"🎬 {title} ({info['imdb']})", callback_data=f"movie_{title}")]
                for title, info in sorted_movies]
    response_text = ("🎖 بهترین‌های تاریخ (10 فیلم برتر):\n"
                     "برای مشاهده جزئیات و پیش‌نمایش، روی دکمه مربوطه کلیک کنید.\n"
                     "⏳ (توجه: پیش‌نمایش به مدت 10 ثانیه نمایش داده می‌شود)")
    await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def movie_preview(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    movie_name = query.data.split("_", 1)[1]
    movie_info = MOVIES.get(movie_name)
    if movie_info:
        notify_text = (
            f"🎥 در حال دانلود پیش‌نمایش «{movie_name}»...\n\n"
            f"📽 عنوان: {movie_name}\n"
            f"⭐ امتیاز IMDB: {movie_info['imdb']}\n"
            f"📝 توضیحات: {movie_info['description']}\n"
            f"💡 پیشنهادی: از این تجربه لذت ببرید!\n\n"
            f"⏳ توجه: این پیش‌نمایش تنها به مدت 10 ثانیه نمایش داده می‌شود. لطفاً در صورت تمایل ذخیره کنید."
        )
        notify_msg = await context.bot.send_message(chat_id=query.message.chat.id, text=notify_text)
        video_msg = await context.bot.send_video(chat_id=query.message.chat.id, video=movie_info['url'], caption=f"🔔 پیش‌نمایش «{movie_name}»")
        await asyncio.sleep(10)
        try:
            await context.bot.delete_message(chat_id=query.message.chat.id, message_id=notify_msg.message_id)
            await context.bot.delete_message(chat_id=query.message.chat.id, message_id=video_msg.message_id)
        except Exception as e:
            logger.error(f"Error deleting preview messages: {e}")
    else:
        await context.bot.send_message(chat_id=query.message.chat.id, text="❌ پیش‌نمایش فیلم یافت نشد!")

async def set_commands(app: Application):
    commands = [
        BotCommand("start", "شروع ربات و دریافت دستورات"),
        BotCommand("search", "جستجوی فیلم (مثال: /search داستان)"),
        BotCommand("bestmovies", "نمایش بهترین فیلم‌ها بر اساس امتیاز IMDB")
    ]
    try:
        # Set commands for default scope (all chats and users)
        from telegram.ext import CommandScope
        await app.bot.set_my_commands(commands, scope=CommandScope.DEFAULT)
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

if __name__ == '__main__': 
    main()