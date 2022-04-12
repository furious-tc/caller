from aiogram.types import ReplyKeyboardMarkup


def menu(who=''):
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    if who != 'юзер':
        menu.row('Отправить код')
    else:
        menu.row('Получить код', 'FAQ')
    return menu