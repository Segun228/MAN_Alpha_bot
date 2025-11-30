from app.handlers.router import user_router as router
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
from app.requests.get.get_business import get_business, get_user_business
from app.requests.get.get_users import get_users
from app.requests.put.put_business import put_business
from app.requests.post.post_business import post_business
from app.requests.delete.delete_business import delete_business
from app.requests.models.post_chat_model import post_chat_model
from app.requests.models.post_document_model import post_document_model
from app.requests.models.post_summarize_model import post_summarize_model
from app.requests.models.post_idea_model import post_idea_model
from app.requests.models.post_analysis_model import post_analysis_model
from app.utils.reaction_handler import ReactionManager



reactioner = ReactionManager()

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
async def cmd_start_admin(message: Message, state: FSMContext, bot:Bot):
    try:
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
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤝"
        )
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
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "restart")
async def callback_start_admin(callback: CallbackQuery, state: FSMContext):
    try:
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
        await callback.message.answer(welcome_text, parse_mode="HTML", reply_markup=inline_keyboards.main)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="inline",
            source="callback",
            payload="restart"
        )
        await callback.answer()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

#===========================================================================================================================
# Регистрация юзера
#===========================================================================================================================


@router.message(CreateUser.start_creating)
async def start_admin_user_create(message: Message, state: FSMContext, bot:Bot):
    try:
        login = message.text
        if login:
            login = login.strip()
        await state.update_data(login = login)
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤝"
        )
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
async def admin_user_enter_email(message: Message, state: FSMContext, bot:Bot):
    try:
        email = message.text
        if email:
            email = email.strip()
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="✍️"
        )
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
        try:
            password = message.text.strip() if message.text else ""
            await state.update_data(password=password)
            hidden_password = "•" * len(password) if password else "не указан"
            try:
                await message.delete()
            except Exception as e:
                logging.exception(e)
                try:
                    await message.edit_text("🔒 [пароль скрыт]")
                except Exception as e:
                    logging.exception(e)
            if len(password) < 6:
                await message.answer("Извините, ваш пароль слишком короткий! Сделайте его больше 6 символов пожалуйста...")
                return
            await message.answer(f"✅ Пароль получен: {hidden_password}")
        except Exception as e:
            logging.exception(e)
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
async def cmd_help(message: Message, bot:Bot):
    try:
        await build_log_message(
            telegram_id=message.from_user.id,
            action="command", 
            source="command",
            payload="help"
        )
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="❤️‍🔥"
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
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)


@router.message(Command("contacts"))
async def cmd_contacts(message: Message, bot:Bot):
    try:
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
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🧑‍💻"
        )
        contacts_text = (
            contacts_text
        )
        await message.reply(
            text=contacts_text,
            reply_markup=inline_keyboards.home,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)

@router.message(Command("info"))
async def cmd_info(message: Message, bot:Bot):
    try:
        await build_log_message(
            telegram_id=message.from_user.id,
            action="command",
            source="command",
            payload="info"
        )
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="✍️"
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
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)

@router.callback_query(F.data == "contacts")
async def contacts_callback(callback: CallbackQuery):
    try:
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
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    try:
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="callback",
            source="menu",
            payload="main_menu"
        )
        await callback.message.answer("Что вас интересует 👇", reply_markup=inline_keyboards.main)
        await callback.answer()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)


#===========================================================================================================================
# Взаимодействие с аккаунтом
#===========================================================================================================================



@router.callback_query(F.data == "request_admin")
async def callback_request_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
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
            tasks.append(bot.send_message(chat_id=admin, text=text, reply_markup= await inline_keyboards.give_acess(user_id=user_id)))
        await callback.message.answer("Права админа запрошены, запрос передан на рассмотрение администраторам")
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "account_menu")
async def account_menu_callback(callback: CallbackQuery):
    try:
        await callback.message.answer("Что вы хотите сделать с вашим аккаунтом? 👤", reply_markup=inline_keyboards.account_menu)
        await callback.answer()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)


@router.callback_query(F.data == "delete_account_confirmation")
async def delete_account_confirmation_callback(callback: CallbackQuery):
    try:
        await callback.message.answer("Вы уверены что хотите удалить аккаунт? 😳 Восстановить записи будет невозможно... 🗑️", reply_markup=inline_keyboards.delete_account_confirmation_menu)
        await callback.answer()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)


@router.callback_query(F.data == "delete_account")
async def delete_account_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await delete_account(telegram_id=callback.from_user.id)
        await state.clear()
        await callback.message.answer("Аккаунт удален 😢", reply_markup=inline_keyboards.restart)
        await callback.answer()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


#===========================================================================================================================
# AI инструменты меню
#===========================================================================================================================


@router.callback_query(F.data == "ai_menu")
async def get_ai_catalogue_menu(callback:CallbackQuery):
    try:
        await callback.message.answer(
            "Какие ИИ инструменты вам интересны?",
            reply_markup=inline_keyboards.catalogue
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)




#===========================================================================================================================
# Каталог
#===========================================================================================================================


@router.callback_query(F.data == "catalogue")
async def get_catalogue_menu(callback:CallbackQuery):
    try:
        current_user = await get_users(
            telegram_id=callback.from_user.id,
            tg_id=callback.from_user.id,
        )
        if not current_user:
            await callback.message.answer(
                "Извините, не удалось получить ваши проекты", 
                reply_markup=inline_keyboards.home
            )
            return
        business_list = current_user.get("businesses")
        if business_list and len(business_list) >= 1:
            await callback.message.answer(
                "Про какой проект вы хотите поговорить?",
                reply_markup=await inline_keyboards.get_business_catalogue(
                    telegram_id = callback.from_user.id,
                    business_list = business_list
                )
            )
        else:
            await callback.message.answer(
                "У вас еще нет созданных бизнесов",
                reply_markup=await inline_keyboards.get_business_catalogue(
                    telegram_id = callback.from_user.id,
                    business_list = business_list
                )
            )
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)




@router.callback_query(F.data.startswith("retrieve_business_"))
async def get_single_business_menu(callback:CallbackQuery):
    try:
        business_id = int(callback.data.split("_")[2])
        current_business = await get_business(
            telegram_id= callback.from_user.id,
            business_id=business_id
        )
        if not current_business:
            await callback.message.answer("Извините, не смогли найти ваш бизнес", reply_markup=inline_keyboards.home)
            return
        await callback.message.answer(
f"""
<b>🏢 {current_business.get("name")}</b>

<code>┌───────────────────────────────</code>
<b>📋 Описание:\n</b>
{current_business.get("description")}
<b>\n</b>
<code>└───────────────────────────────</code>
""", parse_mode="HTML", reply_markup= await inline_keyboards.get_single_business(telegram_id=callback.from_user.id, business = current_business))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)

#===========================================================================================================================
# Business creation
#===========================================================================================================================


@router.callback_query(F.data.startswith("create_business"))
async def create_business_start(callback:CallbackQuery, state:FSMContext):
    try:
        await state.set_state(states.CreateBusiness.start)
        await callback.message.answer(
            "Введите название вашего бизнеса или стартапа. Постарайтесь дать его емко, чтобы оно отражало действительность",
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.CreateBusiness.start)
async def create_business_name(message:Message, state:FSMContext, bot:Bot):
    try:
        name = message.text
        if name is None or not name or not name.strip():
            await message.answer("Извините, не удалось прочесть название, напишите еще раз")
            return
        if len(name) > 500:
            await message.answer("Название слишком большое, постарайтесь описать его лаконичнее")
            return
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🫡"
        )
        await state.update_data(name = name)
        await state.set_state(states.CreateBusiness.description)
        await message.answer(
            """
            <b>📋 Описание вашего бизнеса</b>

            Пожалуйста, распишите подробно всю информацию о вашем бизнесе. Это поможет нам давать максимально точные и полезные рекомендации.

            <u>Основные разделы для заполнения:</u>

            <b>🏢 Формат бизнеса:</b>
            • Онлайн/оффлайн/гибридный
            • B2B/B2C/C2C
            • Продуктовый/сервисный
            • Монобизнес/диверсифицированный

            <b>💰 Продукты и монетизация:</b>
            • Что именно вы продаете (товары/услуги)
            • Основные источники дохода
            • Ценовая политика
            • Целевая аудитория

            <b>💸 Финансовые потоки:</b>
            • Основные статьи доходов
            • Ключевые расходы (постоянные и переменные)
            • Рентабельность
            • Сезонность бизнеса

            <b>🎯 Проблемы и вызовы:</b>
            • Текущие трудности
            • "Узкие места" в процессах
            • Конкурентные challenges
            • Внутренние ограничения

            <b>🚀 Цели развития:</b>
            • <i>Локальные</i> (на 1-6 месяцев)
            • <i>Стратегические</i> (на 1-3 года)
            • Ключевые метрики успеха

            <code>─────────────────────</code>
            <em>Чем детальнее вы опишете каждый пункт, тем более персонализированные рекомендации мы сможем предложить! ✨</em>
            """,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.CreateBusiness.description)
async def create_business_final(message:Message, state:FSMContext, bot:Bot):
    try:
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="✍️"
        )
        description = message.text
        if description is None or not description or not description.strip():
            await message.answer("Извините, не удалось прочесть название, напишите еще раз")
            return
        if len(description) < 20:
            await message.answer("Вы недостаточно раскрыли суть бизнеса, опишите подробнее пожалуйста")
            return
        if len(description) > 3000:
            await message.answer("Вы слишком подробно описали ваш бизнес, извините, многа букав не асилили. Сократите пожалуйста")
            return
        data = await state.get_data()
        name = data.get("name", "Ваш бизнес")
        response = await post_business(
            telegram_id=message.from_user.id,
            name = name,
            description = description
        )
        if not response:
            await message.answer("Извините, не удалось создать модель бизнеса", reply_markup=inline_keyboards.home)
        else:
            await message.answer("Модель успешно создана!", reply_markup= await inline_keyboards.get_business_catalogue(telegram_id = message.from_user.id))
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



#===========================================================================================================================
# Business edit
#===========================================================================================================================


@router.callback_query(F.data.startswith("edit_business_"))
async def edit_business_start(callback:CallbackQuery, state:FSMContext):
    try:
        business_id = int(callback.data.strip().split("_")[2])
        await state.update_data(business_id = business_id)
        await state.set_state(states.EditBusiness.start)
        await callback.message.answer(
            "Введите новое название вашего бизнеса или стартапа",
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.EditBusiness.start)
async def edit_business_name(message:Message, state:FSMContext, bot:Bot):
    try:
        name = message.text
        if name is None or not name or not name.strip():
            await message.answer("Извините, не удалось прочесть название, напишите еще раз")
            return
        if len(name) > 500:
            await message.answer("Название слишком большое, постарайтесь описать его лаконичнее")
            return
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤝"
        )
        await state.update_data(name = name)
        await state.set_state(states.EditBusiness.description)
        await message.answer(
            """
            <b>📋 Описание вашего бизнеса</b>

            Пожалуйста, распишите подробно всю информацию о вашем бизнесе. Это поможет нам давать максимально точные и полезные рекомендации.

            <code>─────────────────────</code>
            <em>Чем детальнее вы опишете каждый пункт, тем более персонализированные рекомендации мы сможем предложить! ✨</em>
            """,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.EditBusiness.description)
async def edit_business_final(message:Message, state:FSMContext, bot:Bot):
    try:
        description = message.text
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🔥"
        )
        if description is None or not description or not description.strip():
            await message.answer("Извините, не удалось прочесть название, напишите еще раз")
            return
        if len(description) < 20:
            await message.answer("Вы недостаточно раскрыли суть бизнеса, опишите подробнее пожалуйста")
            return
        if len(description) > 3000:
            await message.answer("Вы слишком подробно описали ваш бизнес, извините, многа букав не асилили. Сократите пожалуйста")
            return
        data = await state.get_data()
        name = data.get("name", "Ваш бизнес")
        business_id = data.get("business_id")
        if business_id is None:
            raise ValueError("Buisenes id is not loaded")
        response = await put_business(
            telegram_id=message.from_user.id,
            name = name,
            description = description, 
            business_id=business_id
        )
        if not response:
            await message.answer("Извините, не удалось изменить модель бизнеса", reply_markup=inline_keyboards.home)
        else:
            await message.answer("Модель успешно изменена!", reply_markup= await inline_keyboards.get_business_catalogue(telegram_id = message.from_user.id))
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



#===========================================================================================================================
# Business delete
#===========================================================================================================================


@router.callback_query(F.data.startswith("delete_business_"))
async def delete_business_start(callback:CallbackQuery, state:FSMContext):
    try:
        business_id = int(callback.data.strip().split("_")[2])
        await state.update_data(business_id = business_id)
        await state.set_state(states.EditBusiness.start)
        await callback.message.answer(
            "Вы уверены что хотите удалить эту модель бизнеса?",
            reply_markup= await inline_keyboards.confirm(
                object_id=business_id,
                confirm_callback="confirm_delete_business",
                decline_callback="decline_delete_business"
            )
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



@router.callback_query(F.data.startswith("confirm_delete_business"))
async def delete_business_confirm(callback:CallbackQuery, state:FSMContext):
    try:
        business_id = (await state.get_data()).get("business_id")
        response = await delete_business(
            telegram_id=callback.from_user.id,
            business_id=business_id
        )
        if not response:
            await callback.message.answer(
                "Извините, не удалось удалить модель",
                reply_markup=await inline_keyboards.get_business_catalogue(telegram_id = callback.from_user.id)
            )
        else:
            await callback.message.answer(
                "Модель успешно удалена",
                reply_markup=await inline_keyboards.get_business_catalogue(telegram_id = callback.from_user.id)
            )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()




@router.callback_query(F.data.startswith("decline_delete_business"))
async def delete_business_decline(callback:CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        await callback.message.answer(
            "Удаление успешно отменено!",
            reply_markup= await inline_keyboards.get_business_catalogue(
                telegram_id= callback.from_user.id
            )
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



#========================================================================================================================================================================
#========================================================================================================================================================================
# UNIT ECONOMICS BLOCK
#========================================================================================================================================================================
#========================================================================================================================================================================

@router.callback_query(F.data == "unit_menu")
async def catalogue_callback_admin(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="catalogue"
    )
    categories = await get_sets(telegram_id=callback.from_user.id)
    await callback.message.answer("Вот доступные проекты (наборы моделей экономики)👇", reply_markup= await get_catalogue(categories=categories, telegram_id=callback.from_user.id))
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def category_catalogue_callback_admin(callback: CallbackQuery):
    await callback.answer()
    category_id = callback.data.split("_")[1]
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload=f"category_{category_id}"
    )
    categories = await get_sets(telegram_id=callback.from_user.id)
    current_category = None
    if categories is not None:
        for category in categories:
            if str(category.get("id")) == str(category_id):
                current_category = category
                break
    
    if current_category is None or current_category.get("units") is None or current_category.get("units") == []:
        await callback.message.answer("Извините, тут пока пусто, возвращаейтесь позже!", reply_markup= await get_posts(posts=current_category.get("units"), category=current_category ))
        await callback.answer()
        return
    await callback.message.answer("Вот доступные модели юнит-экономики👇", reply_markup= await get_posts(category= current_category ,posts = current_category.get("units", [])))


@router.callback_query(F.data.startswith("post_"))
async def post_catalogue_callback_admin(callback: CallbackQuery):
    await callback.answer()
    post_id = callback.data.split("_")[2]
    category_id = callback.data.split("_")[1]
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload=f"post_{post_id}"
    )
    post_data = await get_post(
        telegram_id=callback.from_user.id,
        post_id=post_id,
        category_id=category_id
    )
    if not post_data:
        await callback.message.answer("Извините, не удалось получить доступ к позиции", reply_markup=inline_keyboards.home)
        return

    message_text = (
        f"📦 **Информация об юните:**\n\n"
        f"**Название:** `{post_data.get('name')}`\n"
        f"**Users:** `{post_data.get('users')}`\n"
        f"**Customers:** `{post_data.get('customers')}`\n"
        f"**AVP:** `{post_data.get('AVP')}`\n"
        f"**APC:** `{post_data.get('APC')}`\n"
        f"**TMS:** `{post_data.get('TMS')}`\n"
        f"**COGS:** `{post_data.get('COGS')}`\n"
        f"**COGS1s:** `{post_data.get('COGS1s')}`\n"
        f"**FC:** `{post_data.get('FC')}`\n"
    )

    await callback.message.answer(
        text=message_text,
        parse_mode="MarkdownV2",
        reply_markup=await inline_keyboards.get_post_menu(
            category_id=category_id,
            post_id=post_id,
        )
    )

#===========================================================================================================================
# Создание сета
#===========================================================================================================================


@router.callback_query(F.data == "create_category")
async def category_create_callback_admin(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="create_category"
    )
    await state.clear()
    await callback.message.answer("Введите название набора моделей экономики")
    await state.set_state(Set.handle_set)
    await callback.answer()


@router.message(Set.handle_set)
async def category_create_callback_admin_description(message: Message, state: FSMContext):
    name = (message.text).strip()
    await state.update_data(name = name)
    await message.answer("Введите описание набора моделей экономики")
    await state.set_state(Set.description)


@router.message(Set.description)
async def category_enter_name_admin(message: Message, state: FSMContext):
    description = (message.text).strip()
    data = await state.get_data()
    name = data.get("name")
    response = await post_set(telegram_id=message.from_user.id, name=name, description= description)
    if not response:
        await message.answer("Извините, не удалось создать набор моделей", reply_markup=inline_keyboards.main)
        return
    await message.answer("Набор моделей создан!", reply_markup= await get_catalogue(telegram_id = message.from_user.id))
    await state.clear()


#===========================================================================================================================
# Создание юнита
#===========================================================================================================================
@router.callback_query(F.data.startswith("create_post_"))
async def post_create_callback_admin(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="create_unit"
    )
    await callback.answer()
    await state.clear()
    category_id = callback.data.split("_")[2]
    await state.update_data(model_set=category_id)
    await callback.message.answer("Введите название модели")
    await state.set_state(Unit.name)


@router.message(Unit.name)
async def post_enter_name_admin(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Введите валидное имя модели")
        return
    await state.update_data(name=name)
    await state.set_state(Unit.users)
    await message.answer("Введите количество привлеченных пользователей")


@router.message(Unit.users)
async def post_enter_description_admin(message: Message, state: FSMContext):
    users = message.text.strip()
    if not users.isdigit():
        await message.answer("Введите валидное число привлеченных пользователей")
        return
    await state.update_data(users=int(users))
    await state.set_state(Unit.customers)
    await message.answer("Введите количество полученных клиентов")


@router.message(Unit.customers)
async def post_enter_price_admin(message: Message, state: FSMContext):
    customers = message.text.strip()
    if not customers.isdigit():
        await message.answer("Введите валидное число полученных клиентов")
        return
    await state.update_data(customers=int(customers))
    await state.set_state(Unit.AVP)
    await message.answer("Введите AVP (Average Value of Payment)")


@router.message(Unit.AVP)
async def post_enter_country_admin(message: Message, state: FSMContext):
    avp = message.text.strip()
    if not avp.isdigit():
        await message.answer("Введите валидное число AVP (Average Value of Payment)")
        return
    await state.update_data(AVP=int(avp))
    await state.set_state(Unit.APC)
    await message.answer("Введите APC (Average Purchase Count)")


@router.message(Unit.APC)
async def post_enter_apc_admin(message: Message, state: FSMContext):
    apc = message.text.strip()
    if not apc.isdigit():
        await message.answer("Введите валидное число APC (Average Purchase Count)")
        return
    await state.update_data(APC=int(apc))
    await state.set_state(Unit.TMS)
    await message.answer("Введите TMS (Total Marketing Spends)")


@router.message(Unit.TMS)
async def post_enter_tms_admin(message: Message, state: FSMContext):
    tms = message.text.strip()
    if not tms.isdigit():
        await message.answer("Введите валидное число TMS (Total Marketing Spends)")
        return
    await state.update_data(TMS=int(tms))
    await state.set_state(Unit.COGS)
    await message.answer("Введите COGS (Cost of goods sold)")


@router.message(Unit.COGS)
async def post_enter_cogs_admin(message: Message, state: FSMContext):
    cogs = message.text.strip()
    if not cogs.isdigit():
        await message.answer("Введите валидное число COGS (Cost of goods sold)")
        return
    await state.update_data(COGS=int(cogs))
    await state.set_state(Unit.COGS1s)
    await message.answer("Введите COGS1s (Cost of goods sold first sale)")


@router.message(Unit.COGS1s)
async def post_enter_cogs1s_admin(message: Message, state: FSMContext):
    cogs1s = message.text.strip()
    if not cogs1s.isdigit():
        await message.answer("Введите валидное число COGS1s (Cost of goods sold first sale)")
        return
    await state.update_data(COGS1s=int(cogs1s))
    await state.set_state(Unit.FC)
    await message.answer("Введите FC (Fixed Costs)")


@router.message(Unit.FC)
async def post_enter_fc_admin(message: Message, state: FSMContext):
    fc = message.text.strip()
    if not fc.isdigit():
        await message.answer("Введите валидное число FC (Fixed Costs)")
        return

    await state.update_data(FC=int(fc))
    data = await state.get_data()
    unit_data = await post_post(
        telegram_id=message.from_user.id,
        category_id=data.get("model_set"),
        name=data.get("name"),
        users=data.get("users"),
        customers=data.get("customers"),
        AVP=data.get("AVP"),
        APC=data.get("APC"),
        TMS=data.get("TMS"),
        COGS=data.get("COGS"),
        COGS1s=data.get("COGS1s"),
        FC=data.get("FC"),
    )
    if not unit_data:
        await message.answer("Ошибка при создании юнита", reply_markup=await get_catalogue(message.from_user.id))
        return

    msg = (
        f"🧩 **Модель успешно создана:**\n\n"
        f"**Название:** `{unit_data.get('name')}`\n"
        f"**Пользователи:** `{unit_data.get('users')}`\n"
        f"**Клиенты:** `{unit_data.get('customers')}`\n"
        f"**AVP:** `{unit_data.get('AVP')}`\n"
        f"**APC:** `{unit_data.get('APC')}`\n"
        f"**TMS:** `{unit_data.get('TMS')}`\n"
        f"**COGS:** `{unit_data.get('COGS')}`\n"
        f"**COGS1s:** `{unit_data.get('COGS1s')}`\n"
        f"**FC:** `{unit_data.get('FC')}`"
    )
    await message.answer(msg, parse_mode="MarkdownV2", reply_markup=await inline_keyboards.get_post_menu(category_id=data.get("model_set"), post_id=unit_data.get("id")))
    await state.clear()

#===========================================================================================================================
# Редактирование сета
#===========================================================================================================================
@router.callback_query(F.data.startswith("edit_category_"))
async def category_edit_callback_admin(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="edit_set"
    )
    await callback.answer()
    await state.clear()
    category_id = callback.data.split("_")[2]
    await state.set_state(Set.handle_edit_set)
    await state.update_data(category_id = category_id)
    await callback.message.answer("Введите новое название сета")


@router.message(Set.handle_edit_set)
async def category_edit_callback_admin_description(message: Message, state: FSMContext):
    name = (message.text).strip()
    await state.update_data(name = name)
    await message.answer("Введите новое описание набора моделей экономики")
    await state.set_state(Set.edit_description)


@router.message(Set.edit_description)
async def category_edit_name_admin(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get("category_id")
    name = data.get("name")
    description = (message.text).strip()
    response = await put_set(telegram_id=message.from_user.id, name=name, category_id=category_id, description=description)
    if not response:
        await message.answer("Извините, не удалось отредактировать сет", reply_markup=inline_keyboards.main)
        return
    await message.answer("Сет отредактирован!", reply_markup=await get_catalogue(telegram_id = message.from_user.id))
    await state.clear()

#===========================================================================================================================
# Редактирование поста
#===========================================================================================================================
@router.callback_query(F.data.startswith("edit_post_"))
async def post_edit_callback_admin(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="edit_post"
    )
    await callback.answer()
    await state.clear()
    category_id, unit_id = callback.data.split("_")[2:]
    await state.update_data(category_id=category_id)
    await state.update_data(post_id=unit_id)
    await callback.message.answer("Введите новое название модели")
    await state.set_state(UnitEdit.handle_edit_unit)


@router.message(UnitEdit.handle_edit_unit)
async def post_edit_name_admin(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Введите валидное имя модели")
        return
    await state.update_data(name=name)
    await state.set_state(UnitEdit.users)
    await message.answer("Введите значение users")


@router.message(UnitEdit.users)
async def post_edit_users_admin(message: Message, state: FSMContext):
    users = message.text.strip()
    if not users.isdigit():
        await message.answer("Введите валидное число пользователей")
        return
    await state.update_data(users=int(users))
    await state.set_state(UnitEdit.customers)
    await message.answer("Введите значение customers")


@router.message(UnitEdit.customers)
async def post_edit_customers_admin(message: Message, state: FSMContext):
    customers = message.text.strip()
    if not customers.isdigit():
        await message.answer("Введите валидное число клиентов")
        return
    await state.update_data(customers=int(customers))
    await state.set_state(UnitEdit.AVP)
    await message.answer("Введите значение AVP")


@router.message(UnitEdit.AVP)
async def post_edit_avp_admin(message: Message, state: FSMContext):
    avp = message.text.strip()
    if not avp.isdigit():
        await message.answer("Введите валидное значение AVP")
        return
    await state.update_data(AVP=int(avp))
    await state.set_state(UnitEdit.APC)
    await message.answer("Введите значение APC")


@router.message(UnitEdit.APC)
async def post_edit_apc_admin(message: Message, state: FSMContext):
    apc = message.text.strip()
    if not apc.isdigit():
        await message.answer("Введите валидное значение APC")
        return
    await state.update_data(APC=int(apc))
    await state.set_state(UnitEdit.TMS)
    await message.answer("Введите значение TMS")


@router.message(UnitEdit.TMS)
async def post_edit_tms_admin(message: Message, state: FSMContext):
    tms = message.text.strip()
    if not tms.isdigit():
        await message.answer("Введите валидное значение TMS")
        return
    await state.update_data(TMS=int(tms))
    await state.set_state(UnitEdit.COGS)
    await message.answer("Введите значение COGS")


@router.message(UnitEdit.COGS)
async def post_edit_cogs_admin(message: Message, state: FSMContext):
    cogs = message.text.strip()
    if not cogs.isdigit():
        await message.answer("Введите валидное значение COGS")
        return
    await state.update_data(COGS=int(cogs))
    await state.set_state(UnitEdit.COGS1s)
    await message.answer("Введите значение COGS1s")


@router.message(UnitEdit.COGS1s)
async def post_edit_cogs1s_admin(message: Message, state: FSMContext):
    cogs1s = message.text.strip()
    if not cogs1s.isdigit():
        await message.answer("Введите валидное значение COGS1s")
        return
    await state.update_data(COGS1s=int(cogs1s))
    await state.set_state(UnitEdit.FC)
    await message.answer("Введите значение FC")


@router.message(UnitEdit.FC)
async def post_edit_fc_admin(message: Message, state: FSMContext):
    fc = message.text.strip()
    if not fc.isdigit():
        await message.answer("Введите валидное значение FC")
        return

    data = await state.get_data()
    logging.warning(f"DATA: {data}")
    unit_data = await put_post(
        telegram_id=message.from_user.id,
        category_id=data.get("category_id"),
        name=data.get("name"),
        users=data.get("users"),
        customers=data.get("customers"),
        AVP=data.get("AVP"),
        APC=data.get("APC"),
        TMS=data.get("TMS"),
        COGS=data.get("COGS"),
        COGS1s=data.get("COGS1s"),
        FC=int(fc),
        post_id=data.get("post_id")
    )

    if not unit_data:
        await message.answer("Ошибка при обновлении модели", reply_markup=await get_catalogue(telegram_id=message.from_user.id))
        return

    await message.answer("Модель успешно обновлена")
    message_text = (
        f"🔧 **Обновлённая модель:**\n\n"
        f"**Название:** `{unit_data.get('name')}`\n"
        f"**Users:** `{unit_data.get('users')}`\n"
        f"**Customers:** `{unit_data.get('customers')}`\n"
        f"**AVP:** `{unit_data.get('AVP')}`\n"
        f"**APC:** `{unit_data.get('APC')}`\n"
        f"**TMS:** `{unit_data.get('TMS')}`\n"
        f"**COGS:** `{unit_data.get('COGS')}`\n"
        f"**COGS1s:** `{unit_data.get('COGS1s')}`\n"
        f"**FC:** `{unit_data.get('FC')}`"
    )

    await message.answer(
        message_text,
        reply_markup=await inline_keyboards.get_post_menu(
            category_id=data.get("category_id"),
            post_id=data.get("post_id")
        ),
        parse_mode="MarkdownV2"
    )
    await state.clear()
#===========================================================================================================================
# Удаление сета   
#===========================================================================================================================

@router.callback_query(F.data.startswith("delete_category_"))
async def category_delete_callback_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    category_id = callback.data.split("_")[2]
    response = await delete_category(telegram_id=callback.from_user.id, category_id=category_id)
    if not response:
        await callback.message.answer("Извините, не удалось удалить категорию", reply_markup=inline_keyboards.main)
        return
    await callback.message.answer("Категория удалена!", reply_markup=await get_catalogue(telegram_id = callback.from_user.id))
    await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="delete_set"
    )


#===========================================================================================================================
# Удаление поста
#===========================================================================================================================

@router.callback_query(F.data.startswith("delete_post_"))
async def post_delete_callback_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    catergory_id, post_id = callback.data.split("_")[2:]
    response = await delete_post(telegram_id=callback.from_user.id, category_id=catergory_id, post_id=post_id)
    if not response:
        await callback.message.answer("Извините, не удалось удалить пост",reply_markup= await get_catalogue(telegram_id = callback.from_user.id))
    await callback.message.answer("Пост успешно удален",reply_markup=await get_catalogue(telegram_id = callback.from_user.id))
    await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="delete_post"
    )


#===========================================================================================================================
# Разрешение доступа
#===========================================================================================================================


@router.callback_query(F.data.startswith("access_give"))
async def give_acess_admin(callback: CallbackQuery, state: FSMContext, bot:Bot):
    request = str(callback.data)
    try:
        user_id = list(request.split("_"))[2]
        if not user_id:
            logging.error("Ошибка предоставления доступа")
            return
        response = await make_admin(
            telegram_id= callback.from_user.id,
            target_user_id= user_id
        )
        if not response:
            logging.error("Ошибка предоставления доступа")
            await bot.send_message(chat_id=int(user_id), text="К сожалению, вам было отказано в предоставлении прав администратора", reply_markup=inline_keyboards.home)
        else:
            logging.info(response)
            await callback.message.answer("Права администратора были успешно предоставлены", reply_markup=inline_keyboards.home)
            await bot.send_message(chat_id=user_id, text="Вам были предоставлены права администратора", reply_markup=inline_keyboards.home)
    except Exception as e:
        logging.error(e)


@router.callback_query(F.data.startswith("access_reject"))
async def reject_acess_admin(callback: CallbackQuery, state: FSMContext, bot:Bot):
    request = str(callback.data)
    try:
        user_id = list(request.split("_"))[2]
        await bot.send_message(chat_id=int(user_id), text="К сожалению, вам было отказано в предоставлении прав администратора", reply_markup=inline_keyboards.home)
    except Exception as e:
        logging.error(e)
    finally:
        await state.clear()

#===========================================================================================================================
# Файловое меню
#===========================================================================================================================


@router.callback_query(F.data == "file_panel")
async def file_panel_admin(callback: CallbackQuery, state: FSMContext, bot:Bot):
    await state.clear()
    await callback.message.edit_text(
        "Выберите интересующую функцию",
        reply_markup= inline_keyboards.file_panel
    )


@router.callback_query(F.data == "get_report")
async def send_report_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):

    await callback.answer("Готовлю ваш отчёт...", show_alert=False)
    docs = await get_report(telegram_id=callback.from_user.id)

    if not docs:
        await callback.message.answer("Извините, не удалось загрузить отчёт. Обратитесь в поддержку.")
        return

    await callback.message.answer(
        "Вот ваш отчёт!"
    )

    await bot.send_document(
        chat_id=callback.message.chat.id,
        document=BufferedInputFile(docs.getvalue(), filename="report.xlsx"),
        reply_markup=inline_keyboards.file_panel
    )
    await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="get_xlsx"
    )



@router.callback_query(F.data == "add_posts")
async def file_add_posts_admin(callback: CallbackQuery, state: FSMContext, bot:Bot):
    
    await callback.message.answer(
        "Это текущие позиции"
    )
    docs = await get_report(telegram_id=callback.from_user.id)
    await bot.send_document(
        chat_id=callback.message.chat.id,
        document=BufferedInputFile(docs.getvalue(), filename="report.xlsx"),
    )
    await callback.message.answer(
        "Вы в режиме добавления позиций. Автоматически будет создан новый набор. Отправте в чат файл с позициями, которые хотите добавить, в таком формате"
    )
    await callback.message.answer(
        "Введите имя новой категории"
    )
    await state.set_state(File.waiting_for_name)
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="post_xlsx"
    )


@router.message(File.waiting_for_name)
async def upload_file_admin(message: Message, state: FSMContext, bot: Bot):
    name = message.text
    await state.update_data(name = name)
    await state.set_state(File.waiting_for_file)
    await message.answer("Отправте боту файл")


@router.message(File.waiting_for_file)
async def upload_add_file_admin(message: Message, state: FSMContext, bot: Bot):
    try:
        file = await bot.get_file(message.document.file_id)
        data = await state.get_data()
        name = data.get("name", "New set")
        file_bytes = await bot.download_file(file.file_path)
        response = await put_report(message.from_user.id, file_bytes, name=name)
        if not response:
            await message.answer(
                "К сожалению, не удалось обработать файл. Убедитесь, что формат файла соответствует установленному."
            )
            await state.clear()
            return
        await message.answer("Файл успешно получен и обработан!", reply_markup= inline_keyboards.file_panel)
        await state.clear()

    except Exception as e:
        await state.clear()
        logging.error(f"Ошибка при обработке Excel: {e}")
        await message.answer("Не удалось обработать файл. Убедитесь, что это корректный Excel (.xlsx).", reply_markup= inline_keyboards.file_panel)
    finally:
        await state.clear()





#==============================================================================================================================================================================================
# Unit analysis
#==============================================================================================================================================================================================


@router.callback_query(F.data.startswith("analise_unit"))
async def analyse_unit_menu(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        await state.clear()
        set_id, unit_id = callback.data.split("_")[2:]
        await callback.message.answer(
            "Меню аналитики текущей модели",
            reply_markup= await inline_keyboards.create_unit_edit_menu(set_id, unit_id)
        )
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Не удалось загрузить аналитический интерфейс, извините", reply_markup= inline_keyboards.main)
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="analize_unit_menu"
    )

def escape_md_v2(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r'\\\1', text)

def format_unit_report(data: dict) -> str:
    get = lambda key: escape_md_v2(data.get(key))
    return f"""
📊 *Отчет по юнит\\-экономике*

*Название:* `{get('name')}`
*Пользователи:* `{get('users')}`
*Клиенты:* `{get('customers')}`
*AVP:* `{get('AVP')}`
*APC:* `{get('APC')}`
*TMS:* `{get('TMS')}`
*COGS:* `{get('COGS')}`
*COGS1s:* `{get('COGS1s')}`
*FC:* `{get('FC')}`

🔢 *Ключевые метрики:*
\\- C1 \\(конверсия\\): {get("C1")}
\\- ARPC \\(доход с клиента\\): {get("ARPC")}
\\- ARPU \\(доход с пользователя\\): {get("ARPU")}
\\- CPA \\(цена привлечения пользователя\\): {get("CPA")}
\\- CAC \\(цена привлечения клиента\\): {get("CAC")}

💰 *Доходность:*
\\- CLTV \\(пожизненная ценность клиента\\): {get("CLTV")}
\\- LTV \\(ценность клиента с учетом C1\\): {get("LTV")}
\\- ROI: {get("ROI")} \\%
\\- UCM \\(юнит\\-contrib\\-маржа\\): {get("UCM")}
\\- CCM \\(клиент\\-contrib\\-маржа\\): {get("CCM")}

📈 *Выручка и прибыль:*
\\- Revenue \\(выручка\\): {get("Revenue")}
\\- Gross Profit \\(валовая прибыль\\): {get("Gross_profit")}
\\- Margin \\(маржа\\): {get("Margin")}
\\- FC \\(постоянные издержки\\): {get("FC")}
\\- Profit \\(прибыль\\): {get("Profit")}

⚖️ *Окупаемость:*
\\- Требуется юнитов до BEP: {get("Required_units_to_BEP")}
\\- BEP \\(точка безубыточности\\): {get("BEP")}

📌 *Прибыльна ли модель:* {"✅ Да" if data.get("CCM", 0)>0 else "❌ Нет"}
""".strip()


def format_bep_report(data: dict) -> str:
    get = lambda key: escape_md_v2(data.get(key, "Undefined"))
    return f"""
📊 *Отчет о точке безубыточности*

💰 *Параметры модели экономики:*
*Название:* `{get('name')}`
*Пользователи:* `{get('users')}`
*Клиенты:* `{get('customers')}`
*AVP:* `{get('AVP')}`
*APC:* `{get('APC')}`
*TMS:* `{get('TMS')}`
*COGS:* `{get('COGS')}`
*COGS1s:* `{get('COGS1s')}`
*FC:* `{get('FC')}`


💰 *Параметры мат модели:*
\\- CCM \\(клиент\\-contrib\\-маржа\\): {get("CCM")}
\\- FC \\(постоянные издержки\\): {get("FC")}

⚖️ *Окупаемость:*
\\- Требуется юнитов до BEP: {get("Required_units_to_BEP")}
\\- BEP \\(точка безубыточности\\): {get("BEP")}

📌 *Прибыльна ли модель:* {"✅ Да" if data.get("CCM", 0)>0 else "❌ Нет"}
""".strip()

@router.callback_query(F.data.startswith("count_unit_economics_"))
async def count_unit_economics(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        print(callback.data.split("_")[2:])
        set_id, unit_id = callback.data.split("_")[3:]
        analysis = await get_unit_report.get_unit_report(
            telegram_id=callback.from_user.id,
            unit_id=unit_id
        )
        if not analysis:
            raise ValueError("Error while generating report")

        await callback.message.answer(
            format_unit_report(analysis[0]),
            reply_markup = inline_keyboards.main,
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Извините, не удалось провести анализ модели", reply_markup= inline_keyboards.main)
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="count_unit_economics"
    )
#==============================================================================================================================================================================================
# Count unit BEP
#==============================================================================================================================================================================================


@router.callback_query(F.data.startswith("count_unit_bep"))
async def count_unit_bep(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        await state.clear()
        set_id, model_id = callback.data.split("_")[3:]
        await callback.answer()

        analysis = await get_unit_report.get_unit_report(
            telegram_id=callback.from_user.id,
            unit_id=model_id
        )

        if not analysis:
            logging.error("Failed to get report")
            await callback.message.answer(
                "К сожалению, не удалось сгенерировать отчёт. Возможно, недостаточно данных 😔",
                reply_markup=inline_keyboards.main)
            await callback.answer()
            return
        analysis = analysis[0]

        if not analysis.get("Required_units_to_BEP") or analysis.get("UCM")<=0:
            await callback.message.answer(
                "К сожалению, данная модель убыточна",
            )
            await callback.message.answer(
                "Точка безубыточности недостижима",
            )
            await callback.message.answer(
                format_bep_report(analysis),
                reply_markup=inline_keyboards.main,
                parse_mode = "MarkdownV2"
            )
            await callback.answer()
            return

        image_bytes_list = await get_unit_bep.get_unit_bep(telegram_id=callback.from_user.id, unit_id=model_id)

        if not image_bytes_list:
            logging.error("Failed to get visual report images from API.")
            await callback.message.answer(
                "К сожалению, не удалось сгенерировать отчёт. Возможно, недостаточно данных 😔",
                reply_markup=inline_keyboards.main)
            await callback.answer()
            return
        
        first_photo = BufferedInputFile(image_bytes_list[0], filename="report_1.png")
        caption_text = "📊 Вот ваш визуальный отчёт о точке безубыточности! 📈"
        analysis = await get_unit_report.get_unit_report(
            telegram_id=callback.from_user.id,
            unit_id=model_id
        )
        if not analysis:
            raise ValueError("Error while generating report")
        await callback.message.answer_photo(
            photo=first_photo,
            caption=caption_text
        )

        for ind, photo_bytes in enumerate(image_bytes_list[1:], start=2):
            if photo_bytes is None:
                continue
            photo_file = BufferedInputFile(photo_bytes, filename=f"report_{ind}.png")
            await callback.message.answer_photo(
                photo=photo_file
            )

        await callback.message.answer(
            format_bep_report(analysis[0]),
            reply_markup=inline_keyboards.main,
            parse_mode = "MarkdownV2"
        )
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Извините, не удалось посчитать точку безубыточности", reply_markup= inline_keyboards.main)
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="count_unit_bep"
    )

#==============================================================================================================================================================================================
# Generate unit report
#==============================================================================================================================================================================================

@router.callback_query(F.data.startswith("generate_report_unit"))
async def generate_unit_report(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        await state.clear()
        set_id, model_id = callback.data.split("_")[3:]
        await callback.answer()

        analysis = await get_unit_report.get_unit_report(
            telegram_id=callback.from_user.id,
            unit_id=model_id
        )

        if not analysis:
            logging.error("Failed to get report")
            await callback.message.answer(
                "К сожалению, не удалось сгенерировать отчёт. Возможно, недостаточно данных 😔",
                reply_markup=inline_keyboards.main)
            await callback.answer()
            return
        analysis = analysis[0]


        await callback.answer("Готовлю ваш отчёт...", show_alert=False)
        docs = await get_unit_exel.get_unit_exel(telegram_id=callback.from_user.id, unit_id=model_id)

        if not docs:
            await callback.message.answer("Извините, не удалось загрузить отчёт. Обратитесь в поддержку.")
            return

        await callback.message.answer(
            "Вот ваш отчёт!"
        )

        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=BufferedInputFile(docs.getvalue(), filename="report.xlsx"),
            reply_markup=inline_keyboards.main
        )
        await state.clear()


    except Exception as e:
        logging.error(e)
        await callback.message.answer("Извините, не удалось посчитать точку безубыточности", reply_markup= inline_keyboards.main)
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="count_bep_unit"
    )


#===========================================================================================================================
# Unit Когортный анализ
#===========================================================================================================================

@router.callback_query(F.data.startswith("cohort_analisis_"))
async def start_cohort_analisis(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        await state.clear()
        set_id, model_id = callback.data.split("_")[2:]
        await callback.answer()
        await state.set_state(Cohort.handle_unit)
        await state.update_data(set_id = set_id)
        await state.update_data(model_id = model_id)

        """
        analysis = await get_unit_report.get_unit_report(
            telegram_id=callback.from_user.id,
            unit_id=model_id
        )
        if not analysis:
            logging.error("Failed to get report")
            await callback.message.answer(
                "К сожалению, не удалось сгенерировать отчёт. Возможно, недостаточно данных 😔",
                reply_markup=inline_keyboards.main)
            await callback.answer()
            return
        analysis = analysis[0]
        """
        await callback.message.answer("Введите процент сохранения аудитории (retention rate, %)")
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)


@router.message(Cohort.handle_unit)
async def continue_cohort_analisis(message:Message, state: FSMContext, bot:Bot):
    retention = message.text
    try:
        if not retention:
            raise ValueError("Invalid retention rate given")
        retention = float(retention)
        await state.update_data(retention = retention)
        await state.set_state(Cohort.retention_rate)
        await message.answer("Введите ожидаемый месячный прирост аудитории (audience growth rate, %)")

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        raise


@router.message(Cohort.retention_rate)
async def finish_cohort_analisis(message:Message, state: FSMContext, bot:Bot):
    growth = message.text
    try:
        if not growth:
            raise ValueError("Invalid retention rate given")
        growth = float(growth)
        data = await state.get_data()
        set_id = data.get("set_id")
        model_id = data.get("model_id")
        retention = data.get("retention")
        await state.clear()
        result = await update_model_cohort_data.update_model_cohort_data(
            telegram_id=message.from_user.id,
            set_id = set_id,
            model_id = model_id,
            retention = retention,
            growth = growth
        )
        if not result:
            raise Exception("Error while patching model")
        
        zip_buf = await get_unit_cohort(
            telegram_id= message.from_user.id,
            unit_id= model_id
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.xlsx')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваш отчет готов!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="count_unit_cohort"
    )

#==============================================================================================================================================================================================
# Set text analisis
#==============================================================================================================================================================================================


@router.callback_query(F.data.startswith("analise_set"))
async def analyse_set_menu_latest(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        await state.clear()
        set_id = callback.data.split("_")[2]
        await callback.message.answer(
            "Меню аналитики текущего сета",
            reply_markup= await inline_keyboards.create_set_edit_menu(set_id)
        )
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Не удалось загрузить аналитический интерфейс, извините", reply_markup= inline_keyboards.main)
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="analize_set"
    )


def format_model_report(data: dict) -> str:
    get = lambda key: escape_md_v2(data.get(key))
    return f"""
📊 *Отчет по юнит\\-экономике*

*Название:* `{get('name')}`
*Пользователи:* `{get('users')}`
*Клиенты:* `{get('customers')}`
*AVP:* `{get('AVP')}`
*APC:* `{get('APC')}`
*TMS:* `{get('TMS')}`
*COGS:* `{get('COGS')}`
*COGS1s:* `{get('COGS1s')}`
*FC:* `{get('FC')}`

🔢 *Ключевые метрики:*
\\- C1 \\(конверсия\\): {get("C1")}
\\- ARPC \\(доход с клиента\\): {get("ARPC")}
\\- ARPU \\(доход с пользователя\\): {get("ARPU")}
\\- CPA \\(цена привлечения пользователя\\): {get("CPA")}
\\- CAC \\(цена привлечения клиента\\): {get("CAC")}

💰 *Доходность:*
\\- CLTV \\(пожизненная ценность клиента\\): {get("CLTV")}
\\- LTV \\(ценность клиента с учетом C1\\): {get("LTV")}
\\- ROI: {get("ROI")} \\%
\\- UCM \\(юнит\\-contrib\\-маржа\\): {get("UCM")}
\\- CCM \\(клиент\\-contrib\\-маржа\\): {get("CCM")}

📈 *Выручка и прибыль:*
\\- Revenue \\(выручка\\): {get("Revenue")}
\\- Gross Profit \\(валовая прибыль\\): {get("Gross_profit")}
\\- Margin \\(маржа\\): {get("Margin")}
\\- FC \\(постоянные издержки\\): {get("FC")}
\\- Profit \\(прибыль\\): {get("Profit")}

⚖️ *Окупаемость:*
\\- Требуется юнитов до BEP: {get("Required_units_to_BEP")}
\\- BEP \\(точка безубыточности\\): {get("BEP")}

📌 *Прибыльна ли модель:* {"✅ Да" if data.get("CCM", 0)>0 else "❌ Нет"}
""".strip()


def format_set_report(data:list):
    result = []
    for i, el in enumerate(data):
        buf = format_unit_report(el)
        if not buf:
            continue
        result.append(buf)
    return result


@router.callback_query(F.data.startswith("count_set_"))
async def count_set_economics(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        set_id = callback.data.split("_")[2]
        analysis = (await set_text_report(
            telegram_id=callback.from_user.id,
            set_id = set_id
        ))
        if not analysis:
            raise ValueError("Error while generating report")
        result = format_set_report(analysis.get("calculated", []))
        for i, el in enumerate(result):
            await callback.message.answer(
                el,
                parse_mode="MarkdownV2"
            )
        await callback.message.answer("Ваш отчет готов!", reply_markup = inline_keyboards.main)
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Извините, не удалось провести анализ модели", reply_markup= inline_keyboards.main)
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="count_unit_set"
    )

#===========================================================================================================================
# Сет визуализация
#===========================================================================================================================


@router.callback_query(F.data.startswith("visual_set"))
async def set_visualize_callback(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        set_id = int(callback.data.split("_")[2])
        await state.clear()
        zip_buf = await set_visualize(
            telegram_id= callback.from_user.id,
            set_id = set_id,
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.xlsx')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=callback.from_user.id, document=document)
        await callback.message.answer("Ваш отчет готов!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )
#===========================================================================================================================
# Сет XLSX отчет
#===========================================================================================================================

@router.callback_query(F.data.startswith("generate_report_set"))
async def set_generate_xlsx_report_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        set_id = int(callback.data.split("_")[3])
        await state.clear()

        xlsx_bytes = await set_generate_report(
            telegram_id=callback.from_user.id,
            set_id=set_id,
        )

        if not xlsx_bytes:
            raise Exception("Error while getting report from the server")

        file_buf = io.BytesIO(xlsx_bytes)
        file_buf.seek(0)

        document = BufferedInputFile(file_buf.read(), filename="report.xlsx")
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=document
        )

        await callback.message.answer("Ваш XLSX отчет готов!", reply_markup=inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Возникла ошибка при анализе", reply_markup=inline_keyboards.main)
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="generate_report_set"
    )
#===========================================================================================================================
# Сет когортный анализ
#===========================================================================================================================

@router.callback_query(F.data.startswith("cohort_set"))
async def start_set_cohort_analisis(callback: CallbackQuery, state: FSMContext, bot:Bot):
    try:
        await state.clear()
        set_id = int(callback.data.split("_")[2])
        await callback.answer()
        await state.set_state(SetCohort.handle_unit)
        await state.update_data(set_id = set_id)

        """
        analysis = await get_unit_report.get_unit_report(
            telegram_id=callback.from_user.id,
            unit_id=model_id
        )
        if not analysis:
            logging.error("Failed to get report")
            await callback.message.answer(
                "К сожалению, не удалось сгенерировать отчёт. Возможно, недостаточно данных 😔",
                reply_markup=inline_keyboards.main)
            await callback.answer()
            return
        analysis = analysis[0]
        """
        await callback.message.answer("Для коректности рузельтатов используется принцип ceteris paribus, параметры будут применены ко всем вложенным моделям")
        await callback.message.answer("Введите процент сохранения аудитории (retention rate, %)")
    except Exception as e:
        logging.error(e)
        await callback.message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)


@router.message(SetCohort.handle_unit)
async def continue_set_cohort_analisis(message:Message, state: FSMContext, bot:Bot):
    retention = message.text
    try:
        if not retention:
            raise ValueError("Invalid retention rate given")
        retention = float(retention)
        await state.update_data(retention = retention)
        await state.set_state(SetCohort.retention_rate)
        await message.answer("Введите ожидаемый месячный прирост аудитории (audience growth rate, %)")

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        raise


@router.message(SetCohort.retention_rate)
async def finish_set_cohort_analisis(message:Message, state: FSMContext, bot:Bot):
    growth = message.text
    try:
        if not growth:
            raise ValueError("Invalid retention rate given")
        growth = float(growth)
        data = await state.get_data()
        set_id = data.get("set_id")
        retention = data.get("retention")
        await state.clear()
        set_data = await retrieve_set(
            telegram_id= message.from_user.id,
            set_id= set_id
        )
        if not set_data:
            raise ValueError("No set data provided")
        models = set_data.get("units")
        if not models:
            raise ValueError("Error receiving models")
        for model in models:
            result = await update_model_cohort_data.update_model_cohort_data(
                telegram_id=message.from_user.id,
                set_id = set_id,
                model_id = model.get("id"),
                retention = retention,
                growth = growth
            )
            if not result:
                raise Exception("Error while patching model")

        zip_buf = await get_set_cohort(
            telegram_id= message.from_user.id,
            set_id=set_id
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.xlsx')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваш отчет готов!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="count_cohort_set"
    )