'''
Если используете Termux:
    pip install wheel
    pkg install libxml2
    pkg install libxslt
    pip intsall gtts
    pip install translators
'''

# необходимые импорты
import os
import logging
import asyncio
import translators
from gtts import gTTS
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
}  # создаем словарь с языками, где ключем будет - названия языка, а значением - код языка !доступно больше языков, читайте документацию translators


# функция на обработку команды /start
async def command_start(message: types.Message, state: FSMContext):

    text = f'Привет, {message.from_user.first_name}!' if message.from_user.language_code == 'ru' \
        else f'Hi, {message.from_user.first_name}!'  # если язык системы русский, отправляем сообщение на русском языке
    await message.answer(
        text=text  # отправляем текст
    )  # в message.from_user.first_name подставится имя пользователя
    await choose_language(message, state)  # сразу вызываем функцию созданную ниже !отправим сообщение и клавиатуру о выборе языка


# отправлка сообщения и клавиатуры выбора языка пользователю
async def choose_language(message: types.Message, state: FSMContext):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)  # создаем клавиатуру
    markup.add(*language.keys())  # добавляем кнопки по ключам словаря language
    text = 'Выбери, на какой язык перевести:' if message.from_user.language_code == 'ru' \
        else 'Choose which language to translate:'  # если язык системы русский, отправляем сообщение на русском языке. Если нет, на английском
    await message.answer(
        text=text,  # отправляем текст
        reply_markup=markup  # отправляем клавиатуру
    )
    await state.set_state('choose_language')  # устанавливаем состояние на choose_language


# сохранение выбранного языка
async def save_language(message: types.Message, state: FSMContext):

    if message.text in language.keys():  # если пользователь нажал на кнопку в клавиатуре
        text = 'Отправь мне текст:' if message.from_user.language_code == 'ru' \
            else 'Send me a text'
        await message.answer(
            text=text,  # отправляем текст
            reply_markup=types.ReplyKeyboardRemove()  # удаляем клавиатуру
        )
        await state.update_data(language=language.get(message.text))  # получаем код языка по ключу и сохраняем в хранилище
        await state.reset_state(with_data=False)  # убираем состояние без удаления данных
    else:  # если отправил другой текст, не тот что на клавиатуре. отправлеям сообщение об ошибке
        text = 'Выбери кнопку ниже.' if message.from_user.language_code == 'ru' \
            else 'Select the button below.'
        await message.answer(
            text=text
        )


async def translate_text(message: types.Message, state: FSMContext):

    try:  # пробуем отправить перевод
        user_data = await state.get_data()  # получаем данные сохраненные в хранилище
        await message.answer_chat_action(
            action=types.ChatActions.TYPING
        )  # answer_chat_action TYPING - создает видимость того, что бот печатает сообщение
        voice_path = f'{message.from_user.id}.ogg'
        to_language = user_data['language']  # передаем язык пользователя в переменную
        text = translators.google(  # вызываем модуль перевода текста
            query_text=message.text,  # передаем текст пользователя
            to_language=to_language  # передаем выбраный язык пользователя
        )
        gTTS(text=text, lang=user_data['language'], slow=False).save(voice_path)  # записываем произношение перевода
        await message.answer_voice(  # отправляем сообщение с аудио произношением и самим переводом
            voice=types.InputFile(voice_path),  # указываем аудио
            caption=text,  # caption добавит описание под аудио !в нашем случае сам перевод
        )
        os.remove(voice_path)  # удаляем записанный аудио файл
    except KeyError:  # если бот был перезагружен, то значение в user_data пропадет, так как данные хранились в ОЗУ
        await choose_language(message, state)  # заново отправляем выбор языка !для того что-бы снова записать значение выбранного языка


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
    await dp.bot.set_my_commands(commands_ru, language_code='ru')  # language_code='ru' устанавливает описание команд на русском языке, пользователям у кого язык стемы указан русский
    await dp.bot.set_my_commands(commands_en)  # для всех других языков, описание на английском


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
