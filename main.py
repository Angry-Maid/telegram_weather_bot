# -*- coding: utf-8 -*-

import asyncio
import os
from datetime import datetime

import aiohttp
import imageio
import telepot
import telepot.aio

import config


bot = telepot.aio.Bot(config.bot_token)


# rewrite for async/await ?
def is_enough_for_gif():
    files = [temp for temp in os.listdir('.') if os.path.isfile(temp) and temp.endswith(".png")]
    if len(files) == 4:
        imageio.mimsave("img.gif", list(map(imageio.read, files)), duration=1)
        for file in files:
            os.remove(file)
    elif len(files) >= 4:
        to_delete = min(files, key=os.path.getctime())
        os.remove(to_delete)
        is_enough_for_gif()


async def get_new_img():
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.site) as resp:
                with open(str(datetime.now().time()).replace(":", "-")[:8] + ".png", "wb") as file:
                    file.write(await resp.read())
        is_enough_for_gif()
        await asyncio.sleep(60 * 15)


async def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    command = msg['text']
    print(str(datetime.now())[:19])
    print("Chat message:", content_type, chat_type, chat_id)
    print("Command:", command)

    if chat_type == "private" and content_type == "text":

        if command == "/info":
            if os.path.isfile("img.gif"):
                with open("img.gif", "rb") as gif_content:
                    await bot.sendDocument(chat_id, document=gif_content)
        elif command == "/current":
            files = [temp for temp in os.listdir('.') if os.path.isfile(temp) and temp.endswith(".png")]
            file = max(files, key=os.path.getctime())
            with open(file, "rb") as png_content:
                await bot.sendPhoto(chat_id, photo=png_content)


def main():
    loop = asyncio.get_event_loop()

    loop.create_task(bot.message_loop(handle))
    loop.create_task(get_new_img())

    loop.run_forever()


if __name__ == "__main__":
    main()
