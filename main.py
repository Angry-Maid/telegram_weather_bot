# -*- coding: utf-8 -*-

import asyncio
import glob
import os
import sqlite3
from datetime import datetime
from itertools import chain
from shutil import copyfile

import aiohttp
import imageio
import telepot
import telepot.aio

import config


subs_db = sqlite3.connect("subscribers.db")
subs_curr = subs_db.cursor()
subscribers = list(chain.from_iterable(subs_curr.execute("SELECT * FROM subscribers")))
bot = telepot.aio.Bot(config.bot_token)
loop = asyncio.get_event_loop()


# rewrite for async/await ?
def is_enough_for_gif():
    files = [file for file in glob.glob("*.png") if file != "current_weather.png"]
    copyfile(files[-1], "current_weather.png")

    flag = True
    while flag:
        if len(files) == 4:
            imageio.mimsave("img.gif", list(map(imageio.imread, files)), duration=1)
            for file in files:
                os.remove(file)
            flag = False
            loop.create_task(send_to_subs())
        elif len(files) >= 4:
            to_delete = min(files, key=os.path.getctime)
            os.remove(to_delete)
            files.remove(to_delete)
        elif len(files) < 4:
            flag = False


async def get_new_img():
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.site) as resp:
                with open(datetime.now().strftime("%H-%M-%S") + ".png", "wb") as file:
                    file.write(await resp.read())
        is_enough_for_gif()
        await asyncio.sleep(60 * 15)


async def send_to_subs():
    with open("img.gif", "rb") as gif_content:
        for sub in subscribers:
            await bot.sendDocument(sub, document=gif_content)


async def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    command = msg['text']
    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    print("Chat message:", content_type, chat_type, str(chat_id))
    print("Command:", command)

    if chat_type == "private" and content_type == "text":

        if command == "/info":
            if os.path.isfile("img.gif"):
                with open("img.gif", "rb") as gif_content:
                    await bot.sendDocument(chat_id, document=gif_content)
        elif command == "/current":
            with open("current_weather.png", "rb") as png_content:
                await bot.sendPhoto(chat_id, photo=png_content)
        elif command == "/sub":
            if chat_id not in subscribers:
                subs_curr.execute("INSERT INTO subscribers (id) VALUES (?)", (chat_id, ))
                subs_db.commit()
                subscribers.append(chat_id)
                await bot.sendMessage(chat_id, "You subscribed to bot")
            else:
                await bot.sendMessage(chat_id, "You already subscribed to bot")
        elif command == "/unsub":
            if chat_id in subscribers:
                subs_curr.execute("DELETE FROM subscribers WHERE id=?", (chat_id, ))
                subs_db.commit()
                subscribers.remove(chat_id)
                await bot.sendMessage(chat_id, "You unsubscribed from bot")
            else:
                await bot.sendMessage(chat_id, "You have not subscribed yet")


def main():
    loop.create_task(bot.message_loop(handle))
    loop.create_task(get_new_img())

    loop.run_forever()


if __name__ == "__main__":
    main()
