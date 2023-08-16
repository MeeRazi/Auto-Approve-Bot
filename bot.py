from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
import os

# Pyrogram configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

ryme = Client(bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
TEXT = "Hello {}, Welcome To {}"
ENABLED_GROUPS = set()  # set of chat IDs where auto-approve is enabled

@ryme.on_chat_join_request(filters.group | filters.channel)
async def autoapprove(client: Client, message: ChatJoinRequest):
    chat_id = message.chat.id
    if chat_id in ENABLED_GROUPS:
        user = message.from_user
        await client.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        await client.send_message(chat_id=chat_id, text=TEXT.format(user.mention, message.chat.title))

@ryme.on_message(filters.command("autoapprove") & filters.group)
async def toggle_autoapprove(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    member = await client.get_chat_member(chat_id=chat_id, user_id=user_id)
    if member.status in ["administrator", "creator"]:
        if len(message.command) > 1:
            action = message.command[1].lower()
            if action == "on":
                ENABLED_GROUPS.add(chat_id)
                await message.reply("Auto approve is now enabled for this group.")
            elif action == "off":
                ENABLED_GROUPS.discard(chat_id)
                await message.reply("Auto approve is now disabled for this group.")
            else:
                await message.reply("Invalid argument. Use 'on' or 'off'.")
        else:
            status = "enabled" if chat_id in ENABLED_GROUPS else "disabled"
            await message.reply(f"Auto approve is currently {status} for this group. Use 'on' or 'off' to toggle.")
    else:
        await message.reply("Only group admins can enable or disable auto approve for this group.")

# Flask configuration
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, this is my Pyrogram bot!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    ryme.run()