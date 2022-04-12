import random
import sys
import config
from aiogram import Bot, Dispatcher, executor, types
import keyboards
import sqlite3
import messages
from states import StateRequest, StateAnswer
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
import phonenumbers

token = config.token

bot = Bot(token, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

try:
    conn = sqlite3.connect('db.sqlite3')
    print('[INFO] База данных подключена!'.encode('cp1252'))
except:
    print('[INFO] Ошибка подключения'.encode('cp1252'))
    sys.exit()

cursor = conn.cursor()

@dp.message_handler(commands=['start'])
async def start_command_handler(msg: types.Message):
    await bot.send_message(msg.from_user.id, f"РАЗРАБОТКА СОФТА: @furious_tc")
    telegram_id = msg.from_user.id
    username = msg.from_user.username
    data = cursor.execute(f"SELECT * FROM users WHERE telegram_id = {telegram_id};")
    user_data = data.fetchone()
    data = cursor.execute(f"SELECT * FROM admins WHERE admin_id = {telegram_id};")
    admin_data = data.fetchone()
    if admin_data is None:
        who = 'юзер'
    else: who = 'админ'

    menu = keyboards.menu(who)
    if user_data is None:
        cursor.execute("""INSERT INTO users(telegram_id, username) VALUES (?, ?);""", (telegram_id, username))
        conn.commit()
        await bot.send_message(msg.from_user.id, f'{messages.MESSAGES["start"]}', reply_markup=menu)
    else:
        await bot.send_message(msg.from_user.id, f'С возвращением!\n\nДля навигации используйте клавиатуру ниже!', reply_markup=menu)


@dp.message_handler(content_types=['text'])
async def message(msg: types.Message):
    data = cursor.execute(f"SELECT * FROM admins WHERE admin_id = {msg.from_user.id};")
    user_data = data.fetchone()
    if msg.text == 'Получить код':
        await StateRequest.request.set()
        await bot.send_message(msg.from_user.id, 'Введите номер телефона!\n<b>Обязательно со знаком "+"</b>')
    elif msg.text == 'FAQ':
        await bot.send_message(msg.from_user.id, f'{messages.MESSAGES["faq"]}')
    elif msg.from_user.id == config.creator and msg.text.__contains__('/admin_add'):

        try:
            id = msg.text.split(" ")[1]
            data = cursor.execute(f"SELECT * FROM admins WHERE admin_id = {id};")
            admin_data = data.fetchone()
            if id.isnumeric() and admin_data is None:
                print('123')
                cursor.execute("""INSERT INTO admins (admin_id) VALUES (?);""", (id, ))
                conn.commit()
                await bot.send_message(msg.from_user.id, 'Админ добавлен!')
        except:
            await bot.send_message(msg.from_user.id, 'Не правильный формат')

    elif msg.from_user.id == config.creator and msg.text.__contains__('/admin_del'):
        try:
            id = msg.text.split(" ")[1]
            data = cursor.execute(f"SELECT * FROM admins WHERE admin_id = {id};")
            admin_data = data.fetchone()
            if id.isnumeric() and admin_data:
                cursor.execute(f"""DELETE FROM admins WHERE admin_id = {id};""")
                conn.commit()
                await bot.send_message(msg.from_user.id, 'Админ удалён!')
        except:
            await bot.send_message(msg.from_user.id, 'Не правильный формат')
    elif user_data:
        if msg.text == 'Отправить код':
            await StateAnswer.answer.set()
            await bot.send_message(msg.from_user.id, 'Введите номер запроса и код!')


@dp.message_handler(state=StateRequest.request)
async def message(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['phone'] = msg.text
            valid = phonenumbers.parse(data['phone'])
            valid = phonenumbers.is_possible_number(valid)
            if valid is True:
                data = cursor.execute(f"SELECT * FROM sms WHERE phone = '{msg.text}';")
                data = data.fetchone()
                if data is None:
                    try:
                        request_number = f'{random.randint(1,999999)}_{random.randint(1,999999)}'
                        cursor.execute("""INSERT INTO sms(request_number, user_id, phone) VALUES (?, ?, ?);""", (f'{request_number}', msg.from_user.id, msg.text))
                        conn.commit()
                        admins = cursor.execute(f"SELECT admin_id FROM admins;")
                        admins = admins.fetchall()
                        for admin in admins:
                            await bot.send_message(admin[0], f'Новый запрос кода, номер {msg.text}\n\nДля ответа нажмите "Отправить код" и введите \n`{request_number}` код', parse_mode='Markdown')
                        await bot.send_message(-1001796413126, f'Новый запрос кода, номер {msg.text}\n\nДля ответа нажмите "Отправить код" и введите \n`{request_number}` код', parse_mode='Markdown')


                    except:
                        await bot.send_message(msg.from_user.id, f'Ошибка добавления в базу!')
                        await state.finish()
                    await bot.send_message(msg.from_user.id, f'Номер отправлен, ожидайте сообщения!\nПримерное время ожидания 2-3 минуты!')
                    await state.finish()
                else:
                    await bot.send_message(msg.from_user.id, f'Номер уже был использован!')
                    await state.finish()
        except:
            await bot.send_message(msg.from_user.id, f'Номер не верный!')
            await state.finish()


@dp.message_handler(state=StateAnswer.answer)
async def message(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['code'] = msg.text
        try:
            info = (data['code']).split(' ')
        except:
            await bot.send_message(msg.from_user.id, f'Формат не верный!')
            await state.finish()
        try:
            data = cursor.execute(f"SELECT user_id, phone FROM sms WHERE request_number = '{info[0]}';").fetchall()
            user_id = data[0][0]
            phone = data[0][1]
            cursor.execute(f"UPDATE sms SET admin_id={msg.from_user.id}, answer_sms='{info[1]}' WHERE request_number = '{info[0]}';")
            conn.commit()
            """
            Удалив 2 строки ниже, база данных будет сохранять только уникальные данные!
            """
            cursor.execute(f"DELETE FROM sms WHERE request_number = '{info[0]}';")
            conn.commit()
            """
            Удалив 2 строки выше, база данных будет сохранять только уникальные данные!
            """
            await bot.send_message(-1001796413126, f'Админ {msg.from_user.id}, отправил код {info[1]}, для номера {phone}!')
            await bot.send_message(msg.from_user.id, 'Код отправлен успешно!')
            await bot.send_message(user_id, f'Ваш код к номеру ({phone}): {info[1]}')
        except:
            await bot.send_message(msg.from_user.id, 'Запрос не найден!')
            await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
