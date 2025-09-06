import os
import logging
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime

import aiohttp
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.chat_action import ChatActionMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7801242693:AAHdcM9ZC22S-oXGWk5MYc1xXD9-7JT21AM")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# Channel information
CHANNEL_USERNAME = "@rxfreezone"  # Your channel username
CHANNEL_URL = "https://t.me/rxfreezone"  # Your channel URL

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Add chat action middleware to show typing status during processing
dp.message.middleware(ChatActionMiddleware())

# Platform logos (you can replace with actual icons)
PLATFORM_ICONS = {
    "youtube": "📺",
    "facebook": "👥",
    "instagram": "📸",
    "tiktok": "🎵",
    "twitter": "🐦",
    "likee": "💃",
    "pinterest": "📌",
    "terabox": "📦",
    "default": "🔗"
}

# User sessions to store temporary data
user_sessions = {}

def create_channel_keyboard():
    """Create inline keyboard with channel join button"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📢 Join Our Channel", 
        url=CHANNEL_URL
    ))
    return builder.as_markup()

def get_channel_note():
    """Create a beautiful note about the channel"""
    note = f"""
⭐ *Thanks for using RX Downloader!* ⭐

🔔 *For more free content and updates, join our channel:*
{CHANNEL_USERNAME}

📥 *We regularly post:*
• Free premium content
• Latest tool updates
• Download tips & tricks
• Exclusive content not available elsewhere

👉 *Tap the button below to join now!*
    """
    return note

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Send welcome message with instructions"""
    welcome_text = f"""
    🎬 *RX Downloader Bot* 🎬

    I can download videos from various social media platforms in high quality!

    🔹 *Supported Platforms:*
    • YouTube 📺
    • Facebook 👥
    • Instagram 📸
    • TikTok 🎵
    • Twitter (X) 🐦
    • Likee 💃
    • Pinterest 📌
    • Terabox 📦

    🔹 *How to use:*
    Just send me a link from any supported platform!

    🔹 *Features:*
    • Multiple resolution options
    • No watermark for supported platforms
    • Audio extraction (MP3)
    • Fast downloads

    🔔 *Don't forget to join our channel for more free content:*
    {CHANNEL_USERNAME}

    ⚠️ Note: For the best experience, send one link at a time.
    """
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=create_channel_keyboard())

@dp.message(Command("help"))
async def send_help(message: types.Message):
    """Send help message"""
    help_text = f"""
    🤖 *RX Downloader Help*

    🔹 *How to use:*
    1. Send a valid URL from any supported platform
    2. I'll analyze the video and show available options
    3. Select your preferred quality/format
    4. Download your media!

    🔹 *Supported platforms:*
    - YouTube (videos, shorts)
    - Facebook (videos, reels)
    - Instagram (posts, reels)
    - TikTok (with/without watermark)
    - Twitter/X (videos)
    - Likee
    - Pinterest
    - Terabox

    🔹 *Features:*
    - Multiple quality options
    - No watermark for TikTok, Likee
    - MP3 audio extraction
    - File size information

    ❓ *Problems?*
    - Make sure the link is valid and public
    - Some content might be restricted by the platform
    - Large files may take longer to process

    🔔 *Join our channel for updates and more free content:*
    {CHANNEL_USERNAME}

    📊 *Stats:* /stats (admin only)
    """
    
    await message.answer(help_text, parse_mode="Markdown", reply_markup=create_channel_keyboard())

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    """Show bot statistics (admin only)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ This command is for administrators only.")
        return
    
    stats_text = f"""
    📊 *RX Downloader Statistics*

    👥 Total users: {len(user_sessions)}
    🏃 Active sessions: {sum(1 for s in user_sessions.values() if 'url' in s)}

    ⚙️ *System Status:* Operational
    📅 Last restart: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(Command("channel"))
async def promote_channel(message: types.Message):
    """Promote the channel"""
    channel_text = f"""
    📢 *Join Our RX Free Zone Channel!* 📢

    We're excited to have you join {CHANNEL_USERNAME} - your hub for all things free and amazing!

    🎁 *What you'll get:*
    • Exclusive content not available anywhere else
    • Early access to new features
    • Premium content for free
    • Download tips and tricks
    • Regular updates about RX Downloader

    👉 *Tap the button below to join now and never miss an update!*

    💬 *Note:* Your support helps us keep providing free services to everyone!
    """
    
    await message.answer(channel_text, parse_mode="Markdown", reply_markup=create_channel_keyboard())

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "facebook.com" in url or "fb.watch" in url:
        return "facebook"
    elif "instagram.com" in url:
        return "instagram"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "twitter.com" in url or "x.com" in url:
        return "twitter"
    elif "likee.video" in url or "likee.com" in url:
        return "likee"
    elif "pinterest." in url:
        return "pinterest"
    elif "terabox." in url:
        return "terabox"
    else:
        return "default"

async def extract_video_info(url: str, platform: str) -> Dict:
    """Extract video information using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    # Platform-specific options
    if platform == "tiktok":
        ydl_opts['format'] = 'best'
    elif platform == "instagram":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract available formats
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') != 'none':  # Video formats
                        resolution = f.get('height', 0)
                        ext = f.get('ext', 'mp4')
                        filesize = f.get('filesize', 0) or f.get('filesize_approx', 0)
                        formats.append({
                            'format_id': f['format_id'],
                            'resolution': resolution,
                            'ext': ext,
                            'filesize': filesize,
                            'format_note': f.get('format_note', '')
                        })
            
            # Get best audio format
            audio_formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # Audio only
                        ext = f.get('ext', 'mp3')
                        filesize = f.get('filesize', 0) or f.get('filesize_approx', 0)
                        audio_formats.append({
                            'format_id': f['format_id'],
                            'ext': ext,
                            'filesize': filesize,
                            'format_note': f.get('format_note', '')
                        })
            
            # Get thumbnail
            thumbnail = info.get('thumbnail') or info.get('thumbnails', [{}])[0].get('url', '')
            
            return {
                'title': info.get('title', 'Video'),
                'duration': info.get('duration', 0),
                'formats': formats,
                'audio_formats': audio_formats,
                'thumbnail': thumbnail,
                'webpage_url': info.get('webpage_url', url),
                'platform': platform,
                'uploader': info.get('uploader', 'Unknown')
            }
    except Exception as e:
        logger.error(f"Error extracting video info: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if not size_bytes:
        return "Unknown size"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def create_quality_keyboard(formats: List[Dict], audio_formats: List[Dict], platform: str, url: str) -> InlineKeyboardMarkup:
    """Create inline keyboard with quality options"""
    builder = InlineKeyboardBuilder()
    
    # Group formats by resolution and get the best format for each resolution
    resolution_map = {}
    for fmt in formats:
        res = fmt['resolution']
        if res and (res not in resolution_map or fmt['filesize'] > resolution_map[res]['filesize']):
            resolution_map[res] = fmt
    
    # Add video quality buttons (highest to lowest)
    resolutions = sorted([r for r in resolution_map.keys() if r], reverse=True)
    for res in resolutions:
        fmt = resolution_map[res]
        size_text = format_file_size(fmt['filesize'])
        builder.row(InlineKeyboardButton(
            text=f"🎥 {res}p ({fmt['ext'].upper()}) - {size_text}",
            callback_data=f"dl_video:{fmt['format_id']}:{url}"
        ))
    
    # Add audio option if available
    if audio_formats:
        best_audio = max(audio_formats, key=lambda x: x['filesize'])
        size_text = format_file_size(best_audio['filesize'])
        builder.row(InlineKeyboardButton(
            text=f"🎵 MP3 Audio - {size_text}",
            callback_data=f"dl_audio:{best_audio['format_id']}:{url}"
        ))
    
    # Add no watermark option for TikTok and Likee
    if platform in ["tiktok", "likee"]:
        builder.row(InlineKeyboardButton(
            text="🚫 No Watermark",
            callback_data=f"dl_nowm:{url}"
        ))
    
    # Add channel join button at the bottom
    builder.row(InlineKeyboardButton(
        text="📢 Join Our Channel for More", 
        url=CHANNEL_URL
    ))
    
    return builder.as_markup()

@dp.message(F.text & F.text.contains("http"))
async def handle_url(message: types.Message):
    """Handle URL messages"""
    url = message.text.strip()
    platform = detect_platform(url)
    icon = PLATFORM_ICONS.get(platform, PLATFORM_ICONS["default"])
    
    # Show typing action
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Send initial message
    processing_msg = await message.answer(f"{icon} Processing your {platform} link...")
    
    # Extract video info
    video_info = await extract_video_info(url, platform)
    if not video_info:
        await processing_msg.edit_text("❌ Failed to process this link. Please make sure it's a valid video URL.")
        return
    
    # Store session data
    user_sessions[message.from_user.id] = {
        'url': url,
        'platform': platform,
        'info': video_info
    }
    
    # Create response with thumbnail and quality options
    caption = f"🎬 *{video_info['title']}*\n\n⏱ Duration: {video_info['duration']} seconds\n📤 Uploader: {video_info['uploader']}\n🔗 Platform: {platform.capitalize()}\n\n{get_channel_note()}"
    
    try:
        # Try to send with thumbnail
        if video_info['thumbnail']:
            await message.answer_photo(
                photo=URLInputFile(video_info['thumbnail']),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=create_quality_keyboard(
                    video_info['formats'], 
                    video_info['audio_formats'], 
                    platform, 
                    url
                )
            )
            await processing_msg.delete()
        else:
            await processing_msg.edit_text(
                text=caption,
                parse_mode="Markdown",
                reply_markup=create_quality_keyboard(
                    video_info['formats'], 
                    video_info['audio_formats'], 
                    platform, 
                    url
                )
            )
    except Exception as e:
        logger.error(f"Error sending thumbnail: {e}")
        await processing_msg.edit_text(
            text=caption,
            parse_mode="Markdown",
            reply_markup=create_quality_keyboard(
                video_info['formats'], 
                video_info['audio_formats'], 
                platform, 
                url
            )
        )

@dp.callback_query(F.data.startswith("dl_"))
async def handle_download(callback: types.CallbackQuery):
    """Handle download requests"""
    data_parts = callback.data.split(":")
    dl_type = data_parts[0]
    format_id = data_parts[1] if len(data_parts) > 1 else ""
    url = data_parts[2] if len(data_parts) > 2 else ""
    
    await callback.answer("Starting download...")
    
    # Show uploading status
    await bot.send_chat_action(callback.message.chat.id, "upload_video")
    
    try:
        if dl_type == "dl_video":
            # Download video with selected quality
            ydl_opts = {
                'format': format_id,
                'outtmpl': f'downloads/%(id)s.%(ext)s',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
            # Send video file with channel promotion
            with open(file_path, 'rb') as video_file:
                await callback.message.answer_video(
                    video=types.BufferedInputFile(
                        video_file.read(),
                        filename=f"{info['title'][:20]}.{info['ext']}"
                    ),
                    caption=f"🎬 {info['title']}\n\n{get_channel_note()}",
                    parse_mode="Markdown",
                    reply_markup=create_channel_keyboard()
                )
            
            # Clean up
            os.remove(file_path)
            
        elif dl_type == "dl_audio":
            # Download audio only
            ydl_opts = {
                'format': format_id,
                'outtmpl': f'downloads/%(id)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
            # Send audio file with channel promotion
            with open(file_path, 'rb') as audio_file:
                await callback.message.answer_audio(
                    audio=types.BufferedInputFile(
                        audio_file.read(),
                        filename=f"{info['title'][:20]}.mp3"
                    ),
                    caption=f"🎵 {info['title']}\n\n{get_channel_note()}",
                    parse_mode="Markdown",
                    reply_markup=create_channel_keyboard()
                )
            
            # Clean up
            os.remove(file_path)
            
        elif dl_type == "dl_nowm":
            # Download without watermark (for TikTok, Likee)
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'downloads/%(id)s.%(ext)s',
            }
            
            # For TikTok, use special parameters to try to get watermark-free version
            if detect_platform(url) == "tiktok":
                ydl_opts['extractor_args'] = {'tiktok': {'watermark': False}}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
            # Send video file with channel promotion
            with open(file_path, 'rb') as video_file:
                await callback.message.answer_video(
                    video=types.BufferedInputFile(
                        video_file.read(),
                        filename=f"{info['title'][:20]}_nowm.{info['ext']}"
                    ),
                    caption=f"🎬 {info['title']} (No Watermark)\n\n{get_channel_note()}",
                    parse_mode="Markdown",
                    reply_markup=create_channel_keyboard()
                )
            
            # Clean up
            os.remove(file_path)
            
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        await callback.message.answer("❌ Error downloading media. Please try again later.")

async def main():
    """Main function"""
    # Create downloads directory if it doesn't exist
    os.makedirs("downloads", exist_ok=True)
    
    # Start the bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())