import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from Token import TOKEN
from aiogram.types import Message

API_TOKEN = TOKEN
authorized_users = set()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
authorized_users = set()
chat_usernames = {}
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
username, password = '', ''

print('SELECT * FROM users WHERE username=? AND password=?')

conn = sqlite3.connect('users.db')
cursor = conn.cursor()


async def check_login(username: str, password: str) -> (bool, int):
    cursor.execute('SELECT id FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    if user:
        return True, user[0]  # Возвращаем True и id пользователя
    else:
        return False, None


@dp.message_handler(commands=['help'])
async def cmd_help(message: Message):
    help_text = (
        "Привет! Я RussianTravelPayment_bot. Вот список доступных команд:\n\n"
        "/start - начать работу с ботом\n"
        "/login - войти в систему (используйте: /login {login} {password})\n"
        "/logout - выйти из системы\n"  # Добавили новую команду
        "/pay - купить голоса (используйте: /pay {кол-во голосов} {сумма}) Цена одного голоса - 100 рублей, максимум голосов - 95\n"
        "/help - получить помощь по командам"
    )
    await message.reply(help_text)


@dp.message_handler(commands=['start'])
async def cmd_start(message: Message):
    await message.reply("❗ Привет! Для входа используй команду /login")


@dp.message_handler(commands=['login'])
async def cmd_login(message: Message):
    user_input = message.text.split()
    if len(user_input) != 3 or user_input[0] != '/login':
        await message.reply("❌ Неверный формат! Используйте: /login login password")
        return

    _, username, password = user_input
    if await check_login(username, password):
        authorized_users.add(username)
        chat_usernames[message.chat.id] = username
        await message.reply('✅ Вход выполнен успешно!')
        # Удаление сообщения пользователя
        await bot.delete_message(message.chat.id, message.message_id)
    else:
        await message.reply('❌ Неверный логин или пароль!')


@dp.message_handler(commands=['logout'])
async def cmd_logout(message: Message):
    username = chat_usernames.get(message.chat.id)
    if username in authorized_users:
        authorized_users.remove(username)
    if message.chat.id in chat_usernames:
        del chat_usernames[message.chat.id]

    await message.reply('✅ Вы успешно вышли из системы!')


async def print_receipt(username: str, votes: int, amount: float):
    receipt = f"Пользователь: {username}\nКоличество голосов: {votes}\nСумма: {amount}\nСпасибо за покупку!"
    return receipt


@dp.message_handler(commands=['pay'])
async def cmd_pay(message: Message):
    # Получаем имя пользователя из словаря
    username = chat_usernames.get(message.chat.id)

    # Проверяем, авторизован ли пользователь
    if username not in authorized_users:
        await message.reply("❌ Пожалуйста, выполните вход с помощью /login перед использованием этой команды.")
        return

    user_input = message.text.split()
    if len(user_input) != 3 or user_input[0] != '/pay':
        await message.reply("❌ Неверный формат! Используйте: /pay {кол-во голосов} {сумма}")
        return
    _, votes, amount = user_input

    try:
        votes = int(votes)
        amount = int(amount)
    except ValueError:
        await message.reply('❌ Неверный формат чисел!')
        return
    if votes > 95:
        await message.reply('❗ Ошибка! Вы не можете купить больше 95 голосов!')
        return
    if amount < votes * 100:
        await message.reply('❗ Ошибка! Цена одного голоса = 100 рублей!')
        return
    # Получаем текущее количество голосов пользователя из базы данных
    cursor.execute('SELECT voices, price FROM users WHERE username = ?', (username,))
    current_voices = cursor.fetchone()[0]
    if current_voices + votes <= 95:
        # Просто добавляем votes в базу данных
        cursor.execute('UPDATE users SET voices = voices + ? WHERE username = ?', (votes, username))
        cursor.execute('UPDATE users SET price = price + ? WHERE username = ?', (amount, username))
    else:
        await message.reply('❗ Ошибка! Колличество голосов не может привышать 95')
        return

    conn.commit()

    await message.reply(f'✅ Платеж успешно проведен: {votes} голосов за {amount} рублей!')

    # Формирование чека
    receipt = await print_receipt(username, votes, amount)

    # Печать чека
    await message.reply(receipt)


@dp.message_handler()
async def echo(message: Message):
    user_input = message.text.split()
    if len(user_input) != 2:
        await message.reply('❌ Неверный формат! Используйте команды')
        return

    username, password = user_input
    if await check_login(username, password):
        await message.reply('✅ Вход выполнен успешно!')
        await bot.delete_message(message.chat.id, message.message_id)
    else:
        await message.reply('Неверный логин или пароль!')


@dp.message_handler(lambda message: message.text.startswith('/'))
async def unknown(message: Message):
    await message.reply("❗ Извините, я не понимаю эту команду.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
