from app.handlers.router import admin_router as router
import logging
import re
import zipfile
import io
import json
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram import F
from typing import Dict, Any
from aiogram.fsm.context import FSMContext
from aiogram import Router, Bot
from aiogram.exceptions import TelegramAPIError
from io import BytesIO
import asyncio

from aiogram.types import InputFile

from app.keyboards import inline_user as inline_keyboards

from app.states.states import Send, CreateUser
from app.states import states
from aiogram.types import BufferedInputFile

from app.filters.IsAdmin import IsAdmin

from app.requests.user.login import login
from app.requests.helpers.get_cat_error import get_cat_error_async
from app.requests.post.post_user import post_user
from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.user.get_alive import get_alive
from app.requests.user.make_admin import make_admin

from app.kafka.utils import build_log_message
from app.requests.user.get_admin_ids import get_admin_ids

import re
from typing import Optional

from app.states import states

def escape_markdown_v2(text: str, version: int = 2) -> str:
    if not text:
        return ""
    if version == 1:
        escape_chars = r'_*`['
    else:
        escape_chars = r'_*[]()~`>#+-=|{}.!'
    pattern = r'([{}])'.format(re.escape(escape_chars))
    escaped_text = re.sub(pattern, r'\\\1', text)
    return escaped_text

#===========================================================================================================================
# Конфигурация основных маршрутов
#===========================================================================================================================


welcome_text = """
<b>🚀 Добро пожаловать в Business Analyst AI!</b>

Я ваш персональный AI-помощник для развития бизнеса. Помогаю анализировать данные, генерировать идеи и находить пути для роста.

<b>🎯 Что я могу для вас сделать:</b>

• <b>📊 Проанализировать</b> ваши бизнес-метрики
• <b>💡 Сгенерировать</b> новые идеи для развития  
• <b>📝 Структурировать</b> отчеты и документы
• <b>🔍 Выявить</b> слабые места и возможности
• <b>🎯 Предложить</b> конкретные шаги для улучшений

<b>📋 Доступные разделы:</b>
- Бизнес-аналитика
- Генерация идей  
- Суммаризация данных
- SWOT-анализ
- Персональные рекомендации

<b>🔍 Используйте команды:</b>
/help - подробная инструкция
/info - о боте и возможностях  
/contacts - связь с поддержкой

<b>Выберите раздел ниже чтобы начать работу! 👇</b>
"""

@router.message(CommandStart())
async def cmd_start_admin(message: Message, state: FSMContext):
    data = await login(telegram_id=message.from_user.id)
    if data is None:
        logging.error("Error while logging admin in")
        await message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    if data.get("status") in (404, 500):
        await state.set_state(CreateUser.start_creating)
        await message.reply("Приветствую Вас! 👋")
        await message.answer("Ой, вы еще не зарегестрированы! Вам будет необходимо пройти короткую регистрацию")
        await message.answer("Введите ваше имя")
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await message.reply("Приветствую, Пользователь! 👋")
    await message.answer("Я ваш личный бизнес асистент")
    await message.answer(welcome_text, parse_mode="HTML")
    await message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="start"
    )
    await state.clear()


@router.callback_query(F.data == "restart")
async def callback_start_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    data = await login(telegram_id=callback.from_user.id)
    if data is None:
        logging.error("Error while logging in")
        await callback.message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    if data.get("status") == 404:
        await state.set_state(CreateUser.start_creating)
        await state.set_state(CreateUser.start_creating)
        await callback.message.reply("Приветствую Вас! 👋")
        await callback.message.answer("Ой, вы еще не зарегестрированы! Вам будет необходимо пройти короткую регистрацию")
        await callback.message.answer("Введите ваше имя")
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await callback.message.reply("Приветствую, Пользователь! 👋")
    await callback.message.answer("Я ваш личный бизнес асистент")
    await callback.message.answer(welcome_text, parse_mode="HTML")
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="inline",
        source="callback",
        payload="restart"
    )
    await callback.answer()

#===========================================================================================================================
# Регистрация юзера
#===========================================================================================================================


@router.message(CreateUser.start_creating)
async def start_admin_user_create(message: Message, state: FSMContext):
    try:
        login = message.text
        if login:
            login = login.strip()
        await state.update_data(login = login)
        await message.answer("Имя получено!")
        await message.answer("Введите ваше почту")
        await state.set_state(CreateUser.login)
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка во время создания пользователя, попробуйте снова", reply_markup=inline_keyboards.restart)
        await state.clear()
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error",
            source="message",
            payload="error"
        )
        return


@router.message(CreateUser.login)
async def admin_user_enter_email(message: Message, state: FSMContext):
    try:
        email = message.text
        if email:
            email = email.strip()
        await state.update_data(email = email)
        await message.answer("Почта получена!")
        await message.answer("Введите ваш пароль")
        await state.set_state(CreateUser.email)
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка во время создания пользователя, попробуйте снова", reply_markup=inline_keyboards.restart)
        await state.clear()
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error",
            source="message",
            payload="error"
        )
        return


@router.message(CreateUser.email)
async def admin_user_enter_password(message: Message, state: FSMContext):
    try:
        password = message.text
        if password:
            password = password.strip()
        await state.update_data(password = password)
        await message.answer("Пароль получен!")
        data = await state.get_data()
        login = data.get("login")
        email = data.get("email")
        result = await post_user(
            telegram_id = message.from_user.id,
            login=login,
            password=password,
            churned=False,
            email=email
        )
        if result is None or not result:
            raise ValueError("Error while sending info to the server")
        await message.answer(
            "Вы успешно зарегались! Нажмите на кнопку чтоб начать диалог...",
            reply_markup=inline_keyboards.restart
        )
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка во время создания пользователя, попробуйте снова", reply_markup=inline_keyboards.restart)
        await state.clear()
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error",
            source="message",
            payload="error"
        )
        return


@router.message(Command("help"))
async def cmd_help(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command", 
        source="command",
        payload="help"
    )
    help_text = """
<b>🤖 Бизнес-Аналитик AI</b> - ваш персональный помощник в развитии бизнеса!

Вы можете просто общаться с ним как с чат-ботом, просто напишите в чат ваш вопрос

<b>🎯 Дополнительные возможности:</b>

• <b>Анализ бизнес-метрик</b> - оценка ключевых показателей
• <b>Генерация идей</b> - креативные решения для роста  
• <b>Суммаризация данных</b> - структурирование отчетов и диалогов
• <b>SWOT-анализ</b> - выявление сильных и слабых сторон
• <b>Рекомендации</b> - персонализированные советы по развитию

<b>📊 Доступные инструменты:</b>
- Анализ финансовых показателей
- Маркетинговая аналитика  
- Оптимизация бизнес-процессов
- Прогнозирование трендов
- Сравнение с конкурентами

<b>💡 Как работать с ботом:</b>
1. Выберите интересующий раздел в меню
2. Следуйте инструкциям бота
3. Получайте структурированные инсайты

Начните с команды /start для доступа ко всем функциям!
"""
    await message.reply(
        text=help_text,
        reply_markup=inline_keyboards.home,
        parse_mode='HTML'
    )

@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command", 
        payload="contacts"
    )
    contacts_text = """
<b>📞 Контакты поддержки</b>

<b>🤝 Реклама и сотрудничество:</b>
@dianabol_metandienon_enjoyer

<b>🤝 Техническая поддержка:</b>
@mattwix

<b>🤝 Проблемы с ИИ:</b>
@andy_andy13

<b>⏰ Время работы поддержки:</b>
Пн-Пт: 8:00 - 18:00 (МСК)
Сб-Вс: по запросу

<b>🚀 Мы поможем:</b>
• Согласовать рекламу и сотрудничество
• Настроить работу с ботом
• Ответим на вопросы по аналитике
• Примем предложения по улучшению
• Решим технические проблемы

<b>📧 Альтернативные способы связи:</b>
Для срочных вопросов используйте Telegram
"""
    contacts_text = (
        contacts_text
    )
    await message.reply(
        text=contacts_text,
        reply_markup=inline_keyboards.home,
        parse_mode='HTML'
    )

@router.message(Command("info"))
async def cmd_info(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="info"
    )
    
    info_text = """
<b>🏢 О Business Analyst AI</b>

<b>🎯 Наша миссия:</b>
Помогать предпринимателям принимать взвешенные бизнес-решения на основе данных и AI-аналитики.

<b>🔍 Что мы делаем:</b>
• Анализируем ваши бизнес-показатели
• Структурируем разрозненные данные  
• Генерируем практические идеи для роста
• Выявляем скрытые возможности
• Предлагаем конкретные шаги для улучшения

<b>📈 Преимущества:</b>
✅ <b>Простота</b> - интуитивный интерфейс
✅ <b>Скорость</b> - мгновенная аналитика  
✅ <b>Точность</b> - на основе современных AI-моделей
✅ <b>Конфиденциальность</b> - ваши данные в безопасности

<b>🛠 Технологии:</b>
• Современные языковые модели (LLM)
• Статистический анализ данных
• Машинное обучение для прогнозирования
• Эмбеддинги для работы с документами

<b>💼 Для кого наш бот:</b>
• Малый и средний бизнес
• Стартапы и предприниматели  
• Фрилансеры и самозанятые
• Все, кто хочет развивать свой бизнес

<b>Начните улучшать свой бизнес уже сегодня! 🚀</b>
"""
    info_text = (
        info_text
    )
    await message.reply(
        text=info_text,
        reply_markup=inline_keyboards.home,
        parse_mode='HTML'
    )

@router.callback_query(F.data == "contacts")
async def contacts_callback(callback: CallbackQuery):
    contacts_text = """
<b>📞 Контакты поддержки</b>

<b>🤝 Реклама и сотрудничество:</b>
@dianabol_metandienon_enjoyer

<b>🤝 Техническая поддержка:</b>
@mattwix

<b>🤝 Проблемы с ИИ:</b>
@andy_andy13

<b>⏰ Время работы поддержки:</b>
Пн-Пт: 8:00 - 18:00 (МСК)
Сб-Вс: по запросу

<b>🚀 Мы поможем:</b>
• Согласовать рекламу и сотрудничество
• Настроить работу с ботом
• Ответим на вопросы по аналитике
• Примем предложения по улучшению
• Решим технические проблемы

<b>📧 Альтернативные способы связи:</b>
Для срочных вопросов используйте Telegram
"""
    contacts_text = (
        contacts_text
    )
    await callback.message.reply(
        text=contacts_text,
        reply_markup=inline_keyboards.home,
        parse_mode='HTML'
    )

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="main_menu"
    )
    await callback.message.answer("Что вас интересует 👇", reply_markup=inline_keyboards.main)
    await callback.answer()


#===========================================================================================================================
# Взаимодействие с аккаунтом
#===========================================================================================================================



@router.callback_query(F.data == "request_admin")
async def callback_request_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    admins = await get_admin_ids(
        telegram_id=callback.from_user.id
    )
    if not admins:
        await callback.message.answer("В сети недостаточно админов чтоб принять у вас заявку", reply_markup=inline_keyboards.home)
        return
    tasks = []
    text = f"Пользоватеь с id {user_id} запросил доступ к правам админа"
    for admin in admins:
        tasks.append(bot.send_message(chat_id=admin, text=text, reply_markup= await inline_keyboards.give_acess(user_id=callback.from_user.id)))
    await callback.message.answer("Права админа запрошены, запрос передан на рассмотрение администраторам")
    await asyncio.gather(*tasks, return_exceptions=True)


@router.callback_query(F.data == "account_menu")
async def account_menu_callback(callback: CallbackQuery):
    await callback.message.answer("Что вы хотите сделать с вашим аккаунтом? 👤", reply_markup=inline_keyboards.account_menu)
    await callback.answer()

@router.callback_query(F.data == "delete_account_confirmation")
async def delete_account_confirmation_callback(callback: CallbackQuery):
    await callback.message.answer("Вы уверены что хотите удалить аккаунт? 😳 Восстановить записи будет невозможно... 🗑️", reply_markup=inline_keyboards.delete_account_confirmation_menu)
    await callback.answer()

@router.callback_query(F.data == "delete_account")
async def delete_account_callback(callback: CallbackQuery, state: FSMContext):
    await delete_account(telegram_id=callback.from_user.id)
    await state.clear()
    await callback.message.answer("Аккаунт удален 😢", reply_markup=inline_keyboards.restart)
    await callback.answer()



#===========================================================================================================================
# Каталог
#===========================================================================================================================


@router.callback_query(F.data == "catalogue")
async def get_catalogue_menu(callaback:CallbackQuery):
    await callaback.message.answer(
        "Вы можете задать специализированные вопросы:",
        reply_markup=inline_keyboards.catalogue
    )


#===========================================================================================================================
# Lawyer
#===========================================================================================================================


@router.callback_query(F.data == "personal_lawyer")
async def get_justice_menu(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer(
        "Подробно опишите интересующий вас вопрос боту. Здесь вам необходимо описать его ОЧЕНЬ точно, так как бот может не понять вольностей интерпритации",
    )
    await state.set_state(states.Lawyer.start)


@router.message(states.Lawyer.start)
async def ask_lawyer_question(message:Message, state:FSMContext):
    user_question = message.text
    if not user_question or not user_question.strip():
        await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
        return
    await message.answer("Я вас понял, дайте секунду подумать...")
    # TODO



#===========================================================================================================================
# Idea Generation
#===========================================================================================================================


@router.callback_query(F.data == "personal_lawyer")
async def get_justice_menu(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer(
        "Подробно опишите интересующий вас вопрос боту. Здесь вам необходимо описать его ОЧЕНЬ точно, так как бот может не понять вольностей интерпритации",
    )
    await state.set_state(states.Lawyer.start)


@router.message(states.Lawyer.start)
async def ask_lawyer_question(message:Message, state:FSMContext):
    user_question = message.text
    if not user_question or not user_question.strip():
        await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
        return
    await message.answer("Я вас понял, дайте секунду подумать...")
    # TODO


#===========================================================================================================================
# Summarise
#===========================================================================================================================


@router.callback_query(F.data == "information_structure")
async def get_information_structure(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer(
        "напишите информацию для структурирования боту",
    )
    await state.set_state(states.Summarizer.start)


@router.message(states.Summarizer.start)
async def summarizer_send_request(message:Message, state:FSMContext):
    user_question = message.text
    if not user_question or not user_question.strip():
        await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
        return
    await message.answer("Я вас понял, дайте секунду сформулировать...")
    # TODO


#===========================================================================================================================
# Business analytics
#===========================================================================================================================

@router.callback_query(F.data == "business_analysis")
async def get_analyzis_type(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer(
        "Какой вид анализа вы хотите провести?",
        reply_markup=inline_keyboards.business_analysis
    )
    await state.set_state(states.Summarizer.start)



#==================
# Business analysis
#==================

@router.callback_query(F.data == "swot_start")
async def swot_analysis(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
    await state.set_state(states.Analysys.swot)
    await state.update_data(type = "swot")
    return


@router.callback_query(F.data == "bmc_start")
async def swot_analysis(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
    await state.set_state(states.Analysys.swot)
    await state.update_data(type = "swot")
    return


@router.callback_query(F.data == "cjm_start")
async def swot_analysis(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
    await state.set_state(states.Analysys.swot)
    await state.update_data(type = "cjm")
    return


@router.callback_query(F.data == "vpc_start")
async def swot_analysis(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
    await state.set_state(states.Analysys.swot)
    await state.update_data(type = "vpc")
    return


@router.callback_query(F.data == "pest_start")
async def swot_analysis(callaback:CallbackQuery, state:FSMContext):
    await callaback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
    await state.set_state(states.Analysys.swot)
    await state.update_data(type = "pest")
    return


@router.message(states.Analysys.swot)
async def analyzer_send_request(message:Message, state:FSMContext):
    user_question = message.text
    if not user_question or not user_question.strip():
        await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
        return
    await message.answer("Я вас понял, дайте секунду проанализировать...")
    data = await state.get_data()
    analyzys_type = data.get("type")
    if not analyzys_type:
        raise ValueError("No type was saved")
    # TODO



