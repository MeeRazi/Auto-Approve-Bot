from flask import Flask
from threading import Thread
from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os

# Pyrogram configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("autoapprove", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
TEXT = "Hello {}, Welcome To {}"
ENABLED_GROUPS = set()  # set of chat IDs where auto-approve is enabled


@bot.on_message(filters.command('start'))
async def start(client, message):
    username = (await client.get_me()).username
    button = [[
        InlineKeyboardButton("➕ Add me in your Group", url=f"http://t.me/{username}?startgroup=none&admin=invite_users"),
        ],[
        InlineKeyboardButton("📌 Updates channel", url=f"https://t.me/botsync"),
    ]]
    await message.reply(
        f"<b>Hello {message.from_user.mention},</b>\n\n<b>Welcome! I'm here to help you manage your group by automatically approving new members. To get started:</b>\n\nAdd me to your group with invite users permissions then send the command /approve in the group, and I'll handle the rest.",
        reply_markup=InlineKeyboardMarkup(button)
    )

@bot.on_chat_join_request(filters.group | filters.channel)
async def autoapprove(client: Client, message: ChatJoinRequest):
    chat_id = message.chat.id
    if chat_id in ENABLED_GROUPS:
        user = message.from_user
        await client.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        await client.send_message(chat_id=chat_id, text=TEXT.format(user.mention, message.chat.title))

@bot.on_message(filters.command("approve"))
async def toggle_autoapprove(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
     
    # Check if the message is from a private chat
    if message.chat.type in [enums.ChatType.PRIVATE]:
        await message.reply("This command can only be used in groups.")
        return

    administrators = []
    async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        administrators.append(m.user.id)

    if user_id not in administrators:
        await message.reply("Only group admins can enable or disable auto approve.")
        return
    
    status = "enabled" if chat_id in ENABLED_GROUPS else "disabled"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ON", callback_data="autoapprove_on"),
         InlineKeyboardButton("OFF", callback_data="autoapprove_off")]
    ])
    await message.reply(f"Auto approve is currently {status} for this group. Use the buttons below to toggle.", reply_markup=markup)

# Handle the callback queries for the inline buttons
@bot.on_callback_query(filters.regex("^autoapprove_(on|off)$"))
async def callback_autoapprove(client: Client, callback_query: CallbackQuery):
    print("Callback received:", callback_query.data)
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    
    try:
        administrators = []
        async for m in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            administrators.append(m.user.id)

        if user_id not in administrators:
            await callback_query.answer("Only group admins can enable or disable auto approve.", show_alert=True)
            return
        
        if callback_query.data == "autoapprove_on":
            ENABLED_GROUPS.add(chat_id)
            await callback_query.message.edit_text("Auto approve is now enabled for this group.")
        elif callback_query.data == "autoapprove_off":
            ENABLED_GROUPS.discard(chat_id)
            await callback_query.message.edit_text("Auto approve is now disabled for this group.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        

# Flask configuration
web = Flask(__name__)

@web.route('/')
def index():
    return "Hello Friend!"

def run():
    web.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.run()