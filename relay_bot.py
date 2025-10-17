import os
import re
import telebot

# --- env vars (must be set in Render) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))     # like -100123456789
OWNER_ID = int(os.getenv("OWNER_ID"))     # your user id

# --- bot init ---
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def is_owner(user_id):
    return user_id == OWNER_ID

# --- /start ---
@bot.message_handler(commands=['start'])
def handle_start(m):
    if not is_owner(m.from_user.id):
        return bot.reply_to(m, "🚫 You are not allowed to use this bot.")
    bot.reply_to(m, "Yo 👋 I'm alive. Use /send <topic_id> <message> or send a file and I'll ask for a topic ID.")

# --- /send for text messages ---
@bot.message_handler(commands=['send'])
def handle_send(m):
    if not is_owner(m.from_user.id):
        return bot.reply_to(m, "🚫 You are not allowed to use this bot.")
    # support: /send 12 Hello world
    match = re.match(r'^/send\s+(\d+)\s+(.+)$', m.text, re.DOTALL)
    if not match:
        return bot.reply_to(m, "Usage: /send <topic_id> <message>\nExample: /send 1 Hello <a href=\"https://example.com\">link</a>")
    topic_id = int(match.group(1))
    msg_text = match.group(2)
    try:
        bot.send_message(GROUP_ID, msg_text, message_thread_id=topic_id)
        bot.reply_to(m, f"✅ Sent to topic {topic_id}")
    except Exception as e:
        bot.reply_to(m, f"❌ Error sending: {e}")

# --- media handler: ask for topic id then post ---
@bot.message_handler(content_types=['photo','video','document','audio','voice'])
def handle_media(m):
    if not is_owner(m.from_user.id):
        return bot.reply_to(m, "🚫 You are not allowed to use this bot.")
    # store the original message in the next-step handler closure
    bot.reply_to(m, "📩 Send me the topic ID where I should post this (send 0 for main chat):")
    bot.register_next_step_handler(m, lambda reply: post_media(reply, m))

def post_media(reply_msg, original_msg):
    # reply_msg = the message with the topic id
    if not is_owner(reply_msg.from_user.id):
        return bot.reply_to(reply_msg, "🚫 You are not allowed to use this bot.")
    try:
        topic_id = int(reply_msg.text.strip())
    except:
        return bot.reply_to(reply_msg, "❌ Invalid topic ID. Send a number like 0 or 12.")
    try:
        if original_msg.content_type == 'photo':
            file_id = original_msg.photo[-1].file_id
            bot.send_photo(GROUP_ID, file_id, caption=original_msg.caption or "", message_thread_id=topic_id)
        elif original_msg.content_type == 'video':
            bot.send_video(GROUP_ID, original_msg.video.file_id, caption=original_msg.caption or "", message_thread_id=topic_id)
        elif original_msg.content_type == 'document':
            bot.send_document(GROUP_ID, original_msg.document.file_id, caption=original_msg.caption or "", message_thread_id=topic_id)
        elif original_msg.content_type == 'audio':
            bot.send_audio(GROUP_ID, original_msg.audio.file_id, caption=original_msg.caption or "", message_thread_id=topic_id)
        elif original_msg.content_type == 'voice':
            bot.send_voice(GROUP_ID, original_msg.voice.file_id, caption=original_msg.caption or "", message_thread_id=topic_id)
        else:
            return bot.reply_to(reply_msg, "❌ Unsupported media type.")
        bot.reply_to(reply_msg, f"✅ Sent media to topic {topic_id}")
    except Exception as e:
        bot.reply_to(reply_msg, f"❌ Error sending media: {e}")

# --- fallback to block non-owner text messages in DM ---
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def protect_private(m):
    if not is_owner(m.from_user.id):
        # silently ignore or send short message
        try:
            bot.reply_to(m, "🚫 You can't use this bot.")
        except:
            pass

if __name__ == "__main__":
    print("🤖 Bot starting...")
    bot.infinity_polling()
