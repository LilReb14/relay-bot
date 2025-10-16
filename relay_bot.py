from telebot import TeleBot, types
import re, os

# --- Environment variables ---
TOKEN = os.getenv("BOT_TOKEN")           # put your bot token in Render's environment vars
GROUP_ID = int(os.getenv("GROUP_ID"))    # your group id
OWNER_ID = int(os.getenv("OWNER_ID"))    # your Telegram user id

bot = TeleBot(TOKEN, parse_mode="HTML")

# --- Memory for media waiting for topic ---
pending_media = {}

def is_owner(user_id):
    return user_id == OWNER_ID

# --- Handle /send command (text messages) ---
@bot.message_handler(commands=['send'])
def send_text(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "🚫 You’re not allowed to use this bot.")
    match = re.match(r'/send\s+(\d+)\s+(.+)', message.text, re.DOTALL)
    if not match:
        bot.reply_to(message, "Format: /send <topic_id> <message>")
        return
    topic_id = int(match.group(1))
    msg_text = match.group(2)
    bot.send_message(GROUP_ID, msg_text, message_thread_id=topic_id)
    bot.reply_to(message, f"✅ Sent to topic {topic_id}")

# --- Handle media (photo/video/file/voice/etc.) ---
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice'])
def handle_media(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "🚫 You’re not allowed to use this bot.")
    msg = bot.reply_to(message, "🧠 Send me the topic ID where I should post this:")
    pending_media[message.chat.id] = message

# --- After owner sends topic id ---
@bot.message_handler(func=lambda m: m.chat.id in pending_media)
def post_media_to_topic(message):
    if not is_owner(message.from_user.id):
        return
    try:
        topic_id = int(message.text.strip())
        original = pending_media.pop(message.chat.id)

        if original.content_type == 'photo':
            file_id = original.photo[-1].file_id
            bot.send_photo(GROUP_ID, file_id, caption=original.caption or "", message_thread_id=topic_id, parse_mode="HTML")

        elif original.content_type == 'video':
            bot.send_video(GROUP_ID, original.video.file_id, caption=original.caption or "", message_thread_id=topic_id, parse_mode="HTML")

        elif original.content_type == 'document':
            bot.send_document(GROUP_ID, original.document.file_id, caption=original.caption or "", message_thread_id=topic_id, parse_mode="HTML")

        elif original.content_type == 'audio':
            bot.send_audio(GROUP_ID, original.audio.file_id, caption=original.caption or "", message_thread_id=topic_id, parse_mode="HTML")

        elif original.content_type == 'voice':
            bot.send_voice(GROUP_ID, original.voice.file_id, caption=original.caption or "", message_thread_id=topic_id, parse_mode="HTML")

        bot.reply_to(message, f"✅ Sent media to topic {topic_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

print("🤖 Bot is running...")
bot.infinity_polling()
