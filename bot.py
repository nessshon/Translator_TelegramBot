# необходимые импорты
import logging
import asyncio
import translators

from aiogram import Dispatcher, Bot, types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import Unauthorized
from aiogram.dispatcher.filters import CommandStart
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()  # в качестве FSM хранилища указываем ОЗУ
token = 'сюда токен бота'  # полученный в @botfather
bot = Bot(token=token)
dp = Dispatcher(bot=bot, storage=storage)  # передаем в storage наше хранилище

language = {
    'Русский': 'ru',
    'English': 'en'
}  # создаем словарь с языками. где ключем будет - названия языка, а значением - код языка


# функция на обработку команды /start
async def command_start(message: types.Message, state: FSMContext):

    text = f'Привет, {message.from_user.first_name}!' if message.from_user.language_code == 'ru' \
        else f'Hi, {message.from_user.first_name}!'  # если язык системы русский, отправляем сообщение на русском языке
    await message.answer(
        text=text  # отправляем текст
    )  # в message.from_user.first_name подставится имя пользователя
    await choose_language(message, state)  # сразу отправим сообщение и клавиатуру о выборе языка


# отправлка сообщения и клавиатуры выбора языка пользователю
async def choose_language(message: types.Message, state: FSMContext):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем клавиатуру
    markup.add(*language.keys())  # добавляем кнопки по ключам словаря language
    text = 'Выбери, на какой язык перевести:' if message.from_user.language_code == 'ru' \
        else 'Choose which language to translate:'  # если язык системы русский, отправляем сообщение на русском языке
    await message.answer(
        text=text,  # отправляем текст
        reply_markup=markup  # отправляем клавиатуру
    )
    await state.set_state('choose_language')  # устанавливаем состояние на choose_language


# сохранение выбранного языка
async def save_language(message: types.Message, state: FSMContext):

    if message.text in language.keys():  # если пользователь нажал на кнпопку в клавиатуре
        text = 'Отправь мне текст:' if message.from_user.language_code == 'ru' \
            else 'Send me a text'  # если язык системы русский, отправляем сообщение на русском языке
        await message.answer(
            text=text,  # отправляем текст
            reply_markup=types.ReplyKeyboardRemove()  # удаляем клавиатуру
        )
        await state.update_data(language=language.get(message.text))  # получаем код языка по ключу и сохраняем в хранилище
        await state.reset_state(with_data=False)  # убираем состояние
    else:  # если отправил другой текст, не тот что на клавиатуре. отправлеям сообщение об ошибке
        text = 'Выбери кнопку ниже.' if message.from_user.language_code == 'ru' \
            else 'Select the button below.'  # если язык системы русский, отправляем сообщение на русском языке
        await message.answer(
            text=text  # отправляем текст
        )


async def translate_text(message: types.Message, state: FSMContext):

    user_data = await state.get_data()  # получаем данные сохраненые в хранилище
    await message.answer_chat_action(
        action=types.ChatActions.TYPING
    )  # answer_chat_action TYPING - отправляет видимость того, что бот печатает сообщение

    to_language = 'ru' if user_data['language'] == 'ru' else 'en'  # если пользователь выбрал русский язык указываем ru если нет en
    text = translators.google(  # вызываем модуль перевода текста
        query_text=message.text,  # передаем текст пользователя
        to_language=to_language  # передаем выбраный язык пользователя
    )
    await message.answer(
        text=text  # отправляем переведенный текст
    )


# устанавливаем команды бота
async def bot_set_commands():

    commands_ru = [  # команды с описанием на русском языке
        types.BotCommand("start", "Перезапустить бота"),
        types.BotCommand("language", "Сменить язык перевода"),
    ]
    commands_en = [  # команды с описанием на английском языке
        types.BotCommand("start", "Restart the bot"),
        types.BotCommand("language", "Change the translation language"),
    ]
    await dp.bot.set_my_commands(commands_ru, language_code='ru')  # установка команд на руском языке !описание будет на русском языке, если язык системы пользователя русский
    await dp.bot.set_my_commands(commands_en)  # установка команд на других языках !описание будет на английском языке, если не установлен русский язык системы


# главная функция - запускает бота
async def main():
    logging.basicConfig(
        format=u'#%(levelname)-8s [%(asctime)s] %(message)s',
        level=logging.INFO
    )  # логгирование
    dp.register_message_handler(
        command_start, CommandStart(), state='*'
    )  # регистрация хендлера на команду /start
    dp.register_message_handler(
        choose_language, commands='language', content_types='text', state='*'
    )  # регистрация хендлера на команду /language
    dp.register_message_handler(
        save_language, content_types='text', state='choose_language'
    )  # регистрация хендлера на сохранения языка, с указанным состояние choose_language
    dp.register_message_handler(
        translate_text, content_types='text'
    )  # регистрация хендлера на все текстовые сообщения !перевод текста

    try:
        await bot_set_commands()  # установка команд
        await dp.start_polling()  # старт поллинга
    except Unauthorized:
        logging.error('Неверный токен!')  # если токен введен неверно
    finally:
        await dp.bot.session.close()  # закрытие сессии бота при остановке


try:
    asyncio.run(main())  # запуск скрипта
except (KeyboardInterrupt, SystemExit):
    logging.error('Бот остановлен!')  # при остановке выводим сообщение
