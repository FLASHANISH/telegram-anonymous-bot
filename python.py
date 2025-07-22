import logging
import random
import string
import re # Import regex module
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup # Import InlineKeyboard
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from collections import deque

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token (Provided by the user)
import os
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', "7547606534:AAHuZOUjwiDAuN5fqKSEZ2_yxmHNEmiugoQ")

# Global data structures
user_queue = deque()
active_chats = {}
user_to_chat_id = {}
blocked_users = set()
user_language_preference = {} # Stores user_id -> language_code (e.g., 'hi', 'en')

# Admin User ID (Replace with your Telegram User ID for admin access)
# IMPORTANT: Your admin username is 'ethicalanish', but the bot needs your numerical User ID.
# Get your User ID from @userinfobot on Telegram.
# Example: ADMIN_ID = 123456789
ADMIN_ID = 5090978662 # <--- YOUR ACTUAL NUMERICAL ADMIN USER ID HAS BEEN SET HERE!

# --- Message Dictionary for Multi-language Support ---
MESSAGES = {
    "hi": { # Hindi
        "start_queue": "आप गुमनाम चैट के लिए कतार में जुड़ गए हैं। हम आपके लिए एक रैंडम उपयोगकर्ता ढूंढ रहे हैं...",
        # MODIFIED: Added report line
        "partner_found": "आपका कनेक्शन हो गया है! अब आप गुमनाम चैट कर सकते हो। चैट आईडी: {chat_id}\nपार्टनर को रिपोर्ट करने के लिए: @complainchat",
        "no_partner_available": "अभी कोई उपयोगकर्ता उपलब्ध नहीं है। कृपया रुक जाइए...",
        # MODIFIED: Full stop message for self
        "chat_stopped_self": "आपने डायलॉग बंद कर दिया है 🙄\nनया पार्टनर ढूंढने के लिए /search टाइप करें। चैट आईडी: {chat_id}\nपार्टनर को रिपोर्ट करने के लिए: @complainchat",
        # MODIFIED: Full stop message for partner
        "chat_stopped_partner": "दूसरा उपयोगकर्ता चैट से निकल गया।\nनया पार्टनर ढूंढने के लिए /search टाइप करें। चैट आईडी: {chat_id}\nपार्टनर को रिपोर्ट करने के लिए: @complainchat",
        "already_in_chat": "आप पहले से ही एक गुमनाम चैट में हैं। चैट खत्म करने के लिए /stop लिखें या नए उपयोगकर्ता के लिए /next लिखें।",
        "not_in_chat": "आप किसी चैट में नहीं हैं।", # Base message for not in chat
        "next_chat_finding": "आपका वर्तमान चैट सत्र समाप्त हो गया है। नया पार्टनर ढूंढा जा रहा है...",
        "report_prompt": "कृपया रिपोर्ट करने के लिए चैट आईडी प्रदान करें। जैसे: /report Chat#ABCDEFGHIJKLMNP0",
        "report_invalid_id": "अमान्य चैट आईडी प्रारूप। कृपया Chat# और 16-अक्षर का अल्फ़ान्यूमेरिक आईडी (जैसे, Chat#ABCDEFGHIJKLMNP0) का उपयोग करें।",
        "report_registered": "आपकी शिकायत दर्ज हो गई है। व्यवस्थापक इसकी समीक्षा करेगा। धन्यवाद!",
        "admin_permission_denied": "आपके पास इस कमांड को उपयोग करने की अनुमति नहीं है।",
        "broadcast_prompt": "कृपया ब्रॉडकास्ट करने के लिए संदेश प्रदान करें। जैसे: /broadcast नमस्ते सभी को!",
        "broadcast_sending": "सभी उपयोगकर्ताओं को संदेश भेजा जा रहा है...",
        "broadcast_sent_count": "ब्रॉडकास्ट संदेश {count} उपयोगकर्ताओं को भेज दिया गया है।",
        "block_prompt": "कृपया ब्लॉक करने के लिए वैध उपयोगकर्ता आईडी प्रदान करें। जैसे: /block 123456789",
        "user_blocked": "उपयोगकर्ता {user_id} को ब्लॉक कर दिया गया है।",
        "user_unblocked": "उपयोगकर्ता {user_id} को अनब्लॉक कर दिया गया है।",
        "user_not_blocked": "उपयोगकर्ता {user_id} ब्लॉक सूची में नहीं है।",
        "blocked_service_abuse": "आपने इस सेवा का गलत इस्तेमाल किया है। आपको ब्लॉक कर दिया गया है।",
        "message_forward_error": "संदेश फॉरवर्ड करने में त्रुटि आ गई। कृपया फिर से कोशिश करें।",
        "settings_placeholder": "⚙️ सेटिंग्स फीचर अभी विकसित किया जा रहा है। कृपया बाद में कोशिश करें।",
        "account_placeholder": "👤 खाता विवरण फीचर अभी विकसित किया जा रहा है। कृपया बाद में कोशिश करें।",
        "link_placeholder": "🔗 गुमनाम चैट में प्रोफाइल साझा करना गुमनामी को तोड़ देगा। इसलिए यह फीचर उपलब्ध नहीं है।",
        "help_text": "📋 कमांड्स: \n"
                     "/start या /search - गुमनाम चैट के लिए कतार में जुड़ें।\n"
                     "/stop - वर्तमान चैट बंद करें।\n"
                     "/next - वर्तमान चैट सत्र समाप्त करें और नए पार्टनर के लिए ढूंढें।\n"
                     "/report Chat#ID - एक चैट को रिपोर्ट करें (Chat#ID को वास्तविक चैट आईडी से बदलें, जैसे, Chat#ABCDEFGHIJKLMNP0)।\n"
                     "/settings - चैट प्राथमिकताएं बदलने के लिए।\n"
                     "/account - अपनी खाता विवरण देखने के लिए।\n"
                     "/link - अपनी प्रोफाइल पार्टनर के साथ साझा करें (गुमनामी टूट जाएगी)।\n"
                     "व्यवस्थापक कमांड्स (केवल व्यवस्थापकों के लिए):\n"
                     "/broadcast <संदेश> - सभी उपयोगकर्ताओं को संदेश भेजें।\n"
                     "/block <user_id> - एक उपयोगकर्ता को ब्लॉक करें।\n"
                     "/unblock <user_id> - एक उपयोगकर्ता को अनब्लॉक करें।",
        "choose_language": "कृपया अपनी भाषा चुनें:",
        "language_set": "आपकी भाषा '{language_name}' पर सेट कर दी गई है।",
        "language_hindi": "हिंदी",
        "language_english": "English",
        "link_blocked": "संदेश में लिंक या @username पाए गए। कृपया लिंक या @username न भेजें।"
    },
    "en": { # English
        "start_queue": "You have been added to the anonymous chat queue. We are looking for a random user for you...",
        # MODIFIED: Added report line
        "partner_found": "You are connected! You can now chat anonymously. Chat ID: {chat_id}\nTo report partner: @complainchat",
        "no_partner_available": "No user is available right now. Please wait...",
        # MODIFIED: Full stop message for self
        "chat_stopped_self": "You stopped the dialog 🙄\nType /search to find a new partner. Chat ID: {chat_id}\nTo report partner: @complainchat",
        # MODIFIED: Full stop message for partner
        "chat_stopped_partner": "The other user left the chat.\nType /search to find a new partner. Chat ID: {chat_id}\nTo report partner: @complainchat",
        "already_in_chat": "You are already in an anonymous chat. Type /stop to end the chat or /next for a new user.",
        "not_in_chat": "You are not in any chat.", # Base message for not in chat
        "next_chat_finding": "Your current chat session has ended. Searching for a new partner...",
        "report_prompt": "Please provide the chat ID to report. E.g.: /report Chat#ABCDEFGHIJKLMNP0",
        "report_invalid_id": "Invalid chat ID format. Please use Chat# and a 16-character alphanumeric ID (e.g., Chat#ABCDEFGHIJKLMNP0).",
        "report_registered": "Your complaint has been registered. Admin will review it. Thank you!",
        "admin_permission_denied": "You do not have permission to use this command.",
        "broadcast_prompt": "Please provide a message to broadcast. E.g.: /broadcast Hello everyone!",
        "broadcast_sending": "Sending message to all users...",
        "broadcast_sent_count": "Broadcast message sent to {count} users.",
        "block_prompt": "Please provide a valid user ID to block. E.g.: /block 123456789",
        "user_blocked": "User {user_id} has been blocked.",
        "user_unblocked": "User {user_id} has been unblocked.",
        "user_not_blocked": "User {user_id} is not in the block list.",
        "blocked_service_abuse": "You have misused this service. You have been blocked.",
        "message_forward_error": "An error occurred while forwarding the message. Please try again.",
        "settings_placeholder": "⚙️ Settings feature is currently under development. Please try again later.",
        "account_placeholder": "👤 Account details feature is currently under development. Please try again later.",
        "link_placeholder": "🔗 Sharing your profile in anonymous chat will break anonymity. Hence, this feature is not available.",
        "help_text": "📋 Commands: \n"
                     "/start or /search - Join the queue for anonymous chat.\n"
                     "/stop - End the current chat.\n"
                     "/next - End current chat session and search for a new partner.\n"
                     "/report Chat#ID - Report a chat (replace Chat#ID with actual chat ID, e.g., Chat#ABCDEFGHIJKLMNP0).\n"
                     "/settings - To change chat preferences.\n"
                     "/account - To view your account details.\n"
                     "/link - Share your profile with partner (anonymity will be broken).\n"
                     "Admin Commands (only for admins):\n"
                     "/broadcast <message> - Send message to all users.\n"
                     "/block <user_id> - Block a user.\n"
                     "/unblock <user_id> - Unblock a user.",
        "choose_language": "Please choose your language:",
        "language_set": "Your language has been set to '{language_name}'.",
        "language_hindi": "Hindi",
        "language_english": "English",
        "link_blocked": "Links or @usernames found in the message. Please do not send links or @usernames."
    }
}

def get_message(user_id: int, key: str, **kwargs) -> str:
    """Retrieves a message in the user's preferred language."""
    lang_code = user_language_preference.get(user_id, "en") # Default to English
    message_template = MESSAGES.get(lang_code, MESSAGES["en"]).get(key, MESSAGES["en"][key])
    return message_template.format(**kwargs)

# --- Helper Functions ---

async def find_partner(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """
    Attempts to find a partner for the given user from the queue.
    If a partner is found, it establishes a new chat.
    """
    if user_id in blocked_users:
        await context.bot.send_message(chat_id=user_id, text=get_message(user_id, "blocked_service_abuse"))
        return

    if user_queue:
        partner_id = user_queue.popleft()
        if partner_id == user_id:
            user_queue.append(partner_id)
            await context.bot.send_message(chat_id=user_id, text=get_message(user_id, "no_partner_available"))
            return

        alphanumeric_chars = string.ascii_letters + string.digits
        random_id_suffix = ''.join(random.choices(alphanumeric_chars, k=16))
        chat_id = f"Chat#{random_id_suffix}"

        active_chats[chat_id] = (user_id, partner_id)
        user_to_chat_id[user_id] = chat_id
        user_to_chat_id[partner_id] = chat_id

        # --- MODIFIED: Add inline keyboard for /stop ---
        keyboard = [[InlineKeyboardButton("Stop Chat /stop", callback_data="command_stop")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user_id, text=get_message(user_id, "partner_found", chat_id=chat_id), reply_markup=reply_markup)
        await context.bot.send_message(chat_id=partner_id, text=get_message(partner_id, "partner_found", chat_id=chat_id), reply_markup=reply_markup)
        # --- END MODIFIED ---
        logger.info(f"New chat established: {chat_id} between {user_id} and {partner_id}")
    else:
        user_queue.append(user_id)
        await context.bot.send_message(chat_id=user_id, text=get_message(user_id, "start_queue"))
        logger.info(f"User {user_id} added to queue.")

async def end_chat(user_id: int, context: ContextTypes.DEFAULT_TYPE, notify_partner: bool = True):
    """
    Ends the chat session for the given user.
    Optionally notifies the partner.
    """
    if user_id in user_to_chat_id:
        chat_id = user_to_chat_id[user_id] # Get chat_id before popping
        user1, user2 = active_chats.pop(chat_id)

        partner_id = user2 if user1 == user_id else user1

        del user_to_chat_id[user_id]
        if partner_id in user_to_chat_id:
            del user_to_chat_id[partner_id]

        # MODIFIED: Pass chat_id to the messages for both users
        await context.bot.send_message(chat_id=user_id, text=get_message(user_id, "chat_stopped_self", chat_id=chat_id))
        if notify_partner:
            await context.bot.send_message(chat_id=partner_id, text=get_message(partner_id, "chat_stopped_partner", chat_id=chat_id))
        logger.info(f"Chat {chat_id} ended. User {user_id} left.")
        return True
    return False

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start (and now /search) command.
    Prompts for language if not set.
    """
    user_id = update.effective_user.id

    if user_id not in user_language_preference:
        keyboard = [
            [
                InlineKeyboardButton(MESSAGES["hi"]["language_hindi"], callback_data="set_lang_hi"),
                InlineKeyboardButton(MESSAGES["en"]["language_english"], callback_data="set_lang_en"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(MESSAGES["en"]["choose_language"], reply_markup=reply_markup)
        return

    if user_id in blocked_users:
        await update.message.reply_text(get_message(user_id, "blocked_service_abuse"))
        return

    if user_id in user_to_chat_id:
        await update.message.reply_text(get_message(user_id, "already_in_chat"))
        return
    
    if user_id in user_queue:
        await update.message.reply_text(get_message(user_id, "start_queue"))
        return

    await find_partner(user_id, context)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /stop command."""
    user_id = update.effective_user.id
    if await end_chat(user_id, context):
        # Message already sent by end_chat
        pass
    else:
        # --- MODIFIED: Add inline keyboard for /start when not in chat ---
        keyboard = [[InlineKeyboardButton("Start Chat /start", callback_data="command_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(get_message(user_id, "not_in_chat"), reply_markup=reply_markup)
        # --- END MODIFIED ---

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /next command."""
    user_id = update.effective_user.id
    if await end_chat(user_id, context):
        await update.message.reply_text(get_message(user_id, "next_chat_finding"))
        await find_partner(user_id, context)
    else:
        # --- MODIFIED: Add inline keyboard for /start when not in chat ---
        keyboard = [[InlineKeyboardButton("Start Chat /start", callback_data="command_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(get_message(user_id, "not_in_chat"), reply_markup=reply_markup)
        # --- END MODIFIED ---

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /report command."""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(get_message(user_id, "report_prompt"))
        return

    chat_id_to_report = context.args[0]
    
    if not chat_id_to_report.startswith("Chat#") or len(chat_id_to_report) != 21 or not all(c.isalnum() for c in chat_id_to_report[5:]):
        await update.message.reply_text(get_message(user_id, "report_invalid_id"))
        return

    await update.message.reply_text(get_message(user_id, "report_registered"))
    logger.info(f"User {user_id} reported chat {chat_id_to_report}")
    
    admin_message = f"🚨 New Report: User {user_id} reported chat {chat_id_to_report}."
    if ADMIN_ID and ADMIN_ID != 123456789: # Only send if ADMIN_ID is set to a valid number
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    user_id = update.effective_user.id
    await update.message.reply_text(get_message(user_id, "help_text"))

# --- Placeholder Commands for Menu Options (Updated for language selection) ---

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /settings command for language selection."""
    user_id = update.effective_user.id
    keyboard = [
        [
            InlineKeyboardButton(MESSAGES["hi"]["language_hindi"], callback_data="set_lang_hi"),
            InlineKeyboardButton(MESSAGES["en"]["language_english"], callback_data="set_lang_en"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_message(user_id, "choose_language"), reply_markup=reply_markup)

async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Placeholder for /account command."""
    user_id = update.effective_user.id
    await update.message.reply_text(get_message(user_id, "account_placeholder"))

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Placeholder for /link command."""
    user_id = update.effective_user.id
    await update.message.reply_text(get_message(user_id, "link_placeholder"))

# --- Admin Commands ---

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command: Sends a message to all active users."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_message(user_id, "admin_permission_denied"))
        return

    if not context.args:
        await update.message.reply_text(get_message(user_id, "broadcast_prompt"))
        return

    message_to_send = "📣 Admin Message: " + " ".join(context.args)
    await update.message.reply_text(get_message(user_id, "broadcast_sending"))

    sent_count = 0
    # Send to users in active chats
    for chat_id in active_chats:
        user1, user2 = active_chats[chat_id]
        try:
            await context.bot.send_message(chat_id=user1, text=message_to_send)
            sent_count += 1
        except Exception as e:
            logger.error(f"Could not send broadcast to {user1}: {e}")
        try:
            await context.bot.send_message(chat_id=user2, text=message_to_send)
            sent_count += 1
        except Exception as e:
            logger.error(f"Could not send broadcast to {user2}: {e}")
            
    # Send to users in queue
    for user_id_in_queue in list(user_queue):
        try:
            await context.bot.send_message(chat_id=user_id_in_queue, text=message_to_send)
            sent_count += 1
        except Exception as e:
            logger.error(f"Could not send broadcast to queued user {user_id_in_queue}: {e}")

    await update.message.reply_text(get_message(user_id, "broadcast_sent_count", count=sent_count))
    logger.info(f"Admin {user_id} broadcasted: '{message_to_send}' to {sent_count} users.")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command: Blocks a user."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_message(user_id, "admin_permission_denied"))
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(get_message(user_id, "block_prompt"))
        return

    target_user_id = int(context.args[0])
    blocked_users.add(target_user_id)
    await update.message.reply_text(get_message(user_id, "user_blocked", user_id=target_user_id))
    logger.info(f"Admin {user_id} blocked user {target_user_id}.")

    if target_user_id in user_to_chat_id:
        await end_chat(target_user_id, context, notify_partner=True)
        await context.bot.send_message(chat_id=target_user_id, text=get_message(target_user_id, "blocked_service_abuse"))
    if target_user_id in user_queue:
        user_queue.remove(target_user_id)
        
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command: Unblocks a user."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(get_message(user_id, "admin_permission_denied"))
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(get_message(user_id, "block_prompt"))
        return

    target_user_id = int(context.args[0])
    if target_user_id in blocked_users:
        blocked_users.remove(target_user_id)
        await update.message.reply_text(get_message(user_id, "user_unblocked", user_id=target_user_id))
        logger.info(f"Admin {user_id} unblocked user {target_user_id}.")
    else:
        await update.message.reply_text(get_message(user_id, "user_not_blocked", user_id=target_user_id))

# --- Message Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forwards messages between connected users, with content filtering."""
    user_id = update.effective_user.id
    message_text = update.effective_message.text

    if user_id in blocked_users:
        return

    # --- Content Filtering: Prevent links and @usernames ---
    # Regex for URLs (http, https, www)
    url_pattern = re.compile(r'(https?://\S+|www\.\S+)', re.IGNORECASE)
    # Regex for @usernames
    username_pattern = re.compile(r'@\w+')

    if url_pattern.search(message_text) or username_pattern.search(message_text):
        await update.message.reply_text(get_message(user_id, "link_blocked"))
        logger.info(f"Blocked message from {user_id} due to link/username: {message_text}")
        return
    # --- End Content Filtering ---

    if user_id in user_to_chat_id:
        chat_id = user_to_chat_id[user_id]
        user1, user2 = active_chats[chat_id]
        
        partner_id = user2 if user1 == user_id else user1

        try:
            await update.message.copy(chat_id=partner_id)
            logger.info(f"Message from {user_id} forwarded to {partner_id} in chat {chat_id}.")
        except Exception as e:
            logger.error(f"Could not forward message from {user_id} to {partner_id} in chat {chat_id}: {e}")
            await update.message.reply_text(get_message(user_id, "message_forward_error"))
    else:
        # --- MODIFIED: Add inline keyboard for /start when not in chat ---
        keyboard = [[InlineKeyboardButton("Start Chat /start", callback_data="command_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(get_message(user_id, "not_in_chat"), reply_markup=reply_markup)
        # --- END MODIFIED ---

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses from inline keyboards."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer() # Acknowledge the query

    if query.data.startswith("set_lang_"):
        lang_code = query.data.split("_")[2]
        user_language_preference[user_id] = lang_code
        
        if lang_code == "hi":
            lang_name = MESSAGES["hi"]["language_hindi"]
        elif lang_code == "en":
            lang_name = MESSAGES["en"]["language_english"]
        else:
            lang_name = "Unknown Language"

        await query.edit_message_text(text=get_message(user_id, "language_set", language_name=lang_name))
        logger.info(f"User {user_id} set language to {lang_code}")
        
        # If the user just set their language via /start, proceed with finding a partner
        if user_id not in user_to_chat_id and user_id not in user_queue:
            await find_partner(user_id, context)
    elif query.data == "command_stop":
        # Simulate /stop command
        await stop(update, context)
    elif query.data == "command_start":
        # Simulate /start command
        await start(update, context)


async def post_init(application: Application) -> None:
    """
    Sets the bot's commands when the bot starts.
    """
    await application.bot.set_my_commands([
        BotCommand("start", "Anonymous chat ke liye queue mein add ho jaiye"),
        BotCommand("search", "Naya partner dhoondein"),
        BotCommand("stop", "Current chat band karein"),
        BotCommand("next", "Current chat session end karein aur naye partner ke liye dhoondein"),
        BotCommand("report", "Ek chat ko report karein"),
        BotCommand("settings", "Chat preferences badalne ke liye"),
        BotCommand("account", "Apni account details dekhne ke liye"),
        BotCommand("link", "Apni profile partner ke saath share karein (anonymity break hogi)"),
        BotCommand("help", "Commands ki list dekhein"),
    ])
    logger.info("Bot commands set successfully.")

def main() -> None:
    """Starts the bot."""
    # Start keep-alive server for Replit
    try:
        from keep_alive import keep_alive
        keep_alive()
        print("✅ Keep-alive server started for 24/7 operation")
    except ImportError:
        print("ℹ️ Running without keep-alive (not on Replit)")
    
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("help", help_command))

    # Add placeholder command handlers for new menu options
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("account", account_command))
    application.add_handler(CommandHandler("link", link_command))

    # Add admin command handlers
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("block", block_user))
    application.add_handler(CommandHandler("unblock", unblock_user))

    # Add message handler (for all non-command messages)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    logger.info("Bot started. Press Ctrl-C to stop.")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")
        print(f"ERROR: The bot encountered an issue and stopped: {e}")

if __name__ == "__main__":
    main()
