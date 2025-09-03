import aiohttp
import random
import string
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "7932127840:AAGu_L3WQA9dizif2wOERnM4ZR9ZAdXgS1A"
CHANNEL_USERNAME = "rxfreezone"   # তোমার চ্যানেল
SMS_API_KEY = "YOUR_SMS_ACTIVATE_API_KEY"     # sms-activate.org থেকে API KEY বসাও

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_emails = {}
user_numbers = {}
user_number_ids = {}

# ------------------- TEMP MAIL -------------------
def generate_email():
    domain_list = ["1secmail.com", "1secmail.org", "1secmail.net"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(domain_list)}"

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"🚫 Join our channel first: {CHANNEL_USERNAME}")
        return
    await message.answer("👋 Welcome to RX TempBot!\n\n"
                         "Commands:\n"
                         "/newmail - Get new email\n"
                         "/inbox - Check mail inbox\n"
                         "/newnumber - Get new temp number\n"
                         "/sms - Check SMS inbox")

# ----- New Temp Mail -----
@dp.message_handler(commands=['newmail'])
async def newmail(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"❌ Please join {CHANNEL_USERNAME} first!")
        return

    email = generate_email()
    user_emails[message.from_user.id] = email
    await message.answer(f"📧 Your temp mail:\n`{email}`\n\nUse /inbox to check mails.", parse_mode="Markdown")

# ----- Mail Inbox -----
@dp.message_handler(commands=['inbox'])
async def inbox(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"❌ Please join {CHANNEL_USERNAME} first!")
        return

    email = user_emails.get(message.from_user.id)
    if not email:
        await message.answer("❌ You don’t have an email yet. Use /newmail first.")
        return

    login, domain = email.split("@")
    async with aiohttp.ClientSession() as session:
        url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
        async with session.get(url) as resp:
            mails = await resp.json()

    if not mails:
        await message.answer("📭 Inbox empty.")
    else:
        text = ""
        for mail in mails:
            mail_id = mail["id"]
            async with aiohttp.ClientSession() as session:
                url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={mail_id}"
                async with session.get(url) as resp:
                    full_mail = await resp.json()
            text += f"📩 From: {full_mail['from']}\nSubject: {full_mail['subject']}\n\n{full_mail['textBody']}\n\n{'-'*30}\n"
        await message.answer(text)

# ------------------- TEMP NUMBER (sms-activate.org) -------------------

# ----- New Temp Number -----
@dp.message_handler(commands=['newnumber'])
async def newnumber(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"❌ Please join {CHANNEL_USERNAME} first!")
        return

    async with aiohttp.ClientSession() as session:
        url = f"https://api.sms-activate.org/stubs/handler_api.php?api_key={SMS_API_KEY}&action=getNumber&service=ot&country=0"
        async with session.get(url) as resp:
            response = await resp.text()

    if "ACCESS_NUMBER" in response:
        parts = response.split(":")
        request_id = parts[1]
        number = parts[2]
        user_numbers[message.from_user.id] = number
        user_number_ids[message.from_user.id] = request_id
        await message.answer(f"📱 Your new temp number: `{number}`\n\nUse /sms to check SMS.", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Failed to get number: {response}")

# ----- SMS Inbox -----
@dp.message_handler(commands=['sms'])
async def sms(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(f"❌ Please join {CHANNEL_USERNAME} first!")
        return

    request_id = user_number_ids.get(message.from_user.id)
    if not request_id:
        await message.answer("❌ You don’t have a number yet. Use /newnumber first.")
        return

    async with aiohttp.ClientSession() as session:
        url = f"https://api.sms-activate.org/stubs/handler_api.php?api_key={SMS_API_KEY}&action=getStatus&id={request_id}"
        async with session.get(url) as resp:
            response = await resp.text()

    if "STATUS_OK" in response:
        code = response.split(":")[1]
        await message.answer(f"📩 Your SMS Code: `{code}`", parse_mode="Markdown")
    else:
        await message.answer(f"⌛ Waiting for SMS...\n\n{response}")

# ------------------- RUN BOT -------------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
