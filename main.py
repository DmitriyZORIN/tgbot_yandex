import logging
from aiogram import Bot, Dispatcher, executor, types
import requests
import json
import socket
import ssl
from telegram import Update as update
from aiogram.types.message import ContentType
from telegram.ext import CallbackContext as contex
from pyzbar.pyzbar import decode
import markups as nav
from db import Database
import os
from PIL import Image
import time

TOKEN = "6279862653:AAH0mNjoikbL3BBB9AA6t4TccaB6t6B8yEM"
YOOTOKEN = "381764678:TEST:55416"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

db = Database("database.db")


def days_to_seconds(days):
    return days * 24 * 60 * 60


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if (not db.user_exists(message.from_user.id)):
        db.add_user(message.from_user.id)
        await bot.send_message(message.from_user.id, "укaжите вaш Hик")
    else:
        await bot.send_message(message.from_user.id, "Bы уже зарегистриованы!", reply_markup=nav.mainMenu)


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def bot_message(message: types.Message):
    if message.chat.type == "private":
        if message.text == 'Профиль':
            user_nickname = "Ваш ник: " + db.get_nickname(message.from_user.id)
            await bot.send_message(message.from_user.id, user_nickname)

        elif message.text == 'Подписка':
            await bot.send_message(message.from_user.id, 'Описание подписки', reply_markup=nav.sub_inline_markup)

        elif message.text == 'Поддержка':
            await bot.send_message(message.from_user.id, "Поддержка: telegramm - @kuzain073\n"
                                                         "mail - DmitriyZOR073@yandex.ru")

        elif message.text == 'О нас':
            await bot.send_message(message.from_user.id,
                                   'LinkCheckerBot - это бот, который даёт пользователям возможность\n'
                                   'проверять ссылки на безопасность по трём параметра:\n'
                                   'Версия ssl сертификата\n'
                                   'Безопасность ссылки по мнению, VirusTotal\n'
                                   'Проверка на redirect\n')

        elif message.text == 'Проверить ссылку':
            await bot.send_message(message.from_user.id, 'Введите ссылку')


        elif 'http' in message.text:
            api_key = 'bf9eb648ecb7a63784289c6792da60cdcb7c6edbdf9ef75116feb5dd6a5e1238'
            url = 'https://www.virustotal.com/vtapi/v2/url/report'

            r = requests.head(message.text, allow_redirects=True)
            print(r.url, requests.head(message.text, allow_redirects=False).url)
            site = r.url

            params = {'apikey': api_key, 'resource': site}
            response = requests.get(url, params=params)
            response_json = json.loads(response.content)
            print(str(response_json['positives']))

            if r.url != requests.head(message.text, allow_redirects=False).url:
                txt = list("Предупреждений: " + str(
                    response_json['positives']) + '/' + str(response_json['total']) + "\n" +
                           "Найден redirect на URL: " + r.url)
                await bot.send_message(message.from_user.id, "".join(txt))
            else:
                try:
                    hostname = r.url[8:-1]
                    context = ssl.create_default_context()
                    print(r.url, hostname)
                    with socket.create_connection((hostname, 443)) as sock:
                        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                            await bot.send_message(message.from_user.id, "Предупреждений: " + str(
                                response_json['positives']) + '/' + str(
                                response_json['total']) + "\n" + "Версия сертификата SSL: " + ssock.version())
                except BaseException:
                    await bot.send_message(message.from_user.id, "Сертификат SSL отсутствует")

        elif 'png' in message.text or 'jpg' in message.text:
            chat_id = update.message.chat_id

            if update.message.photo:
                id_img = update.message.photo[-1].file_id
            else:
                return

            foto = contex.bot.getFile(id_img)

            new_file = contex.bot.get_file(foto.file_id)
            new_file.download('qrcode.png')
            try:
                result = decode(Image.open('qrcode.png'))
                await contex.bot.sendMessage(chat_id=chat_id, text=result[0].data.decode("utf-8"))
                os.remove("qrcode.png")
            except Exception as e:
                await contex.bot.sendMessage(chat_id=chat_id, text=str(e))

        else:
            if db.get_signup(message.from_user.id) == "setnickname":
                if (len(message.text) > 15):
                    await bot.send_message(message.from_user.id, "Никнейм не должен привышать 15 символов")
                elif "@" in message.text or "/" in message.text:
                    await bot.send_message(message.from_user.id, "Вы ввели запрещённый символ")
                else:
                    db.set_nickname(message.from_user.id, message.text)
                    db.set_signup(message.from_user.id, "done")
                    await bot.send_message(message.from_user.id, "Регистрация прошла успешно!",
                                           reply_markup=nav.mainMenu)
            else:
                await bot.send_message(message.from_user.id, "Команда не распознана")


@dp.callback_query_handler(text="submonth")
async def submonth(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_invoice(chat_id=call.from_user.id, title="Оформление подписки",
                           description="Тестовое описание товара", payload="month_sub", provider_token=YOOTOKEN,
                           currency='RUB', start_parameter='test_bot', prices=[{'label': 'Руб', 'amount': 15000}])


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    if message.successful_payment.invoice_payload == "month_sub":
        time_sub = int(time.time()) + days_to_seconds(30)
        db.set_time_sub(message.from_user.id, time_sub)
        await bot.send_message(message.from_user.id, "Вам выдана подписка на месяц!")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
