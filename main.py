from pytube import YouTube
import asyncio
import re
from pathlib import Path
import subprocess
import config
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters.builtin import CommandStart, Regexp
from aiogram.utils.callback_data import CallbackData

from scheduler_func import scheduler

API_TOKEN = config.KEY_BOT
URL_STORE = config.URL_STORE
PATH_MEDIA = Path(config.TEMP_MEDIA_FILES)
STORE = Path(config.STORE)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
cd_walk = CallbackData("call_", "action", "url")


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Let`s get started"),
            types.BotCommand("help", "Help"),
        ]
    )


def keyboard(link):
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(f"Video mp4 360p", callback_data=cd_walk.new(action='v?360', url=link)),
        InlineKeyboardButton(f"Video mp4 720p", callback_data=cd_walk.new(action='v?720', url=link)),
        InlineKeyboardButton(f"Video mp4 1080p", callback_data=cd_walk.new(action='v?1080', url=link)),
        InlineKeyboardButton(f"Video mp4 Highest", callback_data=cd_walk.new(action='v?hi', url=link)),
        InlineKeyboardButton(f"Audio mp3 128kbps", callback_data=cd_walk.new(action='a?128', url=link)),
        InlineKeyboardButton(f"Audio mp3 256kbps", callback_data=cd_walk.new(action='a?256', url=link)),
    )


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await message.answer(f"Hi, {message.from_user.full_name}.\n"
                         f"I will help you to get videos and audios from YouTube.\n")
    await message.answer("*Now give me ⬇️url⬆️ you want to.*  🔊📲",
                         parse_mode=types.ParseMode.MARKDOWN)


@dp.message_handler(Regexp(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9("
                           r")@:%_\+.~#?&//=]*)"))
async def get_type(message: types.Message):
    link = message.text.split("/")[-1]
    print(link)
    await message.answer(f"What to do?", reply_markup=keyboard(link))


@dp.callback_query_handler(cd_walk.filter())
async def media_worker(call: types.CallbackQuery, callback_data: dict):
    await bot.send_message(call.from_user.id, text="Processing...  💡")
    action = callback_data.get('action').split("?")
    url = "https://www.youtube.com/" + callback_data.get('url')
    media = "video" if action[0] == "v" else "audio"
    quality = "Hi" if media == "video" and action[1] == "hi" else action[1]
    print(url, media, quality, sep="\n")

    if media == "audio":
        file_name = download(url, media, quality)
        media_file = PATH_MEDIA.joinpath(file_name)
        converter(media_file, quality)
        media_file = media_file.replace(media_file.with_suffix(".mp3"))
        media_file = media_file.replace(STORE.joinpath("_".join(re.findall(r"[\w.]+", media_file.name))))
        print(media_file)
        await bot.send_message(call.from_user.id, text=f'Mp3 video is created.\n'
                                                       f'Download it. Soon it will be deleted.\n'
                                                       f'{URL_STORE}{media_file.name}')
    elif media == "video":
        file_name = download(url, media, quality)
        media_file = PATH_MEDIA.joinpath(file_name)
        # move file to store
        media_file = media_file.replace(STORE.joinpath("_".join(re.findall(r"[\w.]+", media_file.name))))
        await bot.send_message(call.from_user.id, text=f'Mp4 video is created.\n'
                                                       f'Download it. Soon it will be deleted.\n'
                                                       f'{URL_STORE}{media_file.name}')


def download(link, media, quality):

    youtube_object = YouTube(link)

    if media == "video":
        if quality == "Hi":
            youtube_object = youtube_object.streams.filter(progressive=True).last()
        else:
            youtube_object = youtube_object.streams.filter(progressive=True).get_by_resolution(resolution=quality + "p")

        try:
            youtube_object.download(str(PATH_MEDIA))
        except Exception as er:
            print("An error has occurred", er)
        print("Download is completed successfully")

    elif media == "audio":
        youtube_object = youtube_object.streams.get_audio_only()
        try:
            youtube_object.download(str(PATH_MEDIA))
        except Exception as er:
            print("An error has occurred", er)
        print("Download is completed successfully")

    return youtube_object.default_filename


def converter(file_name, quality='128'):
    subprocess.run([
        'ffmpeg',
        '-y',
        '-i',
        file_name,
        '-ab', quality,
        file_name
    ])


async def on_startup(dp: Dispatcher):
    await set_default_commands(dp)
    asyncio.create_task(scheduler())
    print("The bot started")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
