from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

btnProfile = KeyboardButton('Профиль')
btnSub = KeyboardButton('Подписка')
btnSupport = KeyboardButton('Поддержка')
btnAbout_us = KeyboardButton('О нас')
btnUrl = KeyboardButton('Проверить ссылку')
mainMenu = ReplyKeyboardMarkup(resize_keyboard=True)
mainMenu.add(btnProfile, btnSub, btnSupport, btnAbout_us, btnUrl)

sub_inline_markup = InlineKeyboardMarkup(row_width=1)
btnSubMonth = InlineKeyboardButton(text='Месяц - 150 рублей', callback_data='submonth')
sub_inline_markup.insert(btnSubMonth)



