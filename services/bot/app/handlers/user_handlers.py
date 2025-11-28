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
async def cmd_start_admin(message: Message, state: FSMContext):
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
        try:
            password = message.text.strip() if message.text else ""
            await state.update_data(password=password)
            hidden_password = "•" * len(password) if password else "не указан"
            await message.answer(f"✅ Пароль получен: {hidden_password}")
            try:
                await message.delete()
            except Exception as e:
                logging.exception(e)
                try:
                    await message.edit_text("🔒 [пароль скрыт]")
                except Exception as e:
                    logging.exception(e)
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
async def cmd_help(message: Message):
    try:
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
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)


@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
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
async def cmd_info(message: Message):
    try:
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
        logging.info(str(current_business))
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
async def create_business_name(message:Message, state:FSMContext):
    try:
        name = message.text
        if name is None or not name or not name.strip():
            await message.answer("Извините, не удалось прочесть название, напишите еще раз")
            return
        if len(name) > 500:
            await message.answer("Название слишком большое, постарайтесь описать его лаконичнее")
            return
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
            emoji="❤️"
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
        logging.info(callback.data)
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
async def edit_business_name(message:Message, state:FSMContext):
    try:
        name = message.text
        if name is None or not name or not name.strip():
            await message.answer("Извините, не удалось прочесть название, напишите еще раз")
            return
        if len(name) > 500:
            await message.answer("Название слишком большое, постарайтесь описать его лаконичнее")
            return
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
async def edit_business_final(message:Message, state:FSMContext):
    try:
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
        logging.info(callback.data)
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




#===========================================================================================================================
# Lawyer
#===========================================================================================================================


@router.callback_query(F.data == "personal_lawyer")
async def get_justice_menu(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "Подробно опишите интересующий вас вопрос боту. Здесь вам необходимо описать его ОЧЕНЬ точно, так как бот может не понять вольностей интерпритации",
        )
        await callback.message.answer(
            "Операция очень тяжелая, при ошибке нажмите 'Повторить'",
        )
        await state.set_state(states.Lawyer.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.message(states.Lawyer.start)
async def ask_lawyer_question(message: Message, state: FSMContext):
    try:
        user_question = message.text
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        
        await message.answer("Я вас понял, дайте секунду подумать...")
        await state.update_data(user_question=user_question)
        
        result = await post_document_model(
            telegram_id=message.from_user.id,
            text=user_question
        )
        
        if result is None:
            await message.answer(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
        if not isinstance(result, dict):
            await message.answer(
                result,
                reply_markup=inline_keyboards.main
            )
        else:
            raise Exception("eeror while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await message.answer(
            "Извините, бот немножко устал, попробуйте позже 😢", 
            reply_markup=inline_keyboards.retry_keyboard
        )
        await state.set_state(states.Lawyer.start)


@router.callback_query(F.data == "retry_question", states.Lawyer.start)
async def retry_question(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Повторяю запрос...")
        state_data = await state.get_data()
        user_question = state_data.get('user_question')
        
        if not user_question:
            await callback.message.answer(
                "Не удалось найти предыдущий вопрос. Пожалуйста, задайте вопрос заново.",
                reply_markup=inline_keyboards.home
            )
            await state.clear()
            return
        await callback.message.edit_text("Повторяю запрос, секунду...")
        result = await post_document_model(
            telegram_id=callback.from_user.id,
            text=user_question
        )
        if result is None:
            await callback.message.edit_text(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
            
        if not isinstance(result, dict):
            await callback.message.edit_text(
                result,
                reply_markup=inline_keyboards.main
            )
        else:
            raise Exception("eeror while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)

        await callback.message.edit_text(
            "Снова произошла ошибка. Попробовать еще раз?",
            reply_markup=inline_keyboards.retry_keyboard
        )

#===========================================================================================================================
# Idea Generation
#===========================================================================================================================

@router.callback_query(F.data == "idea_generation")
async def generate_idea_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer("Пожалуйста, опишите ваш вопрос или идею для анализа:")
        await state.set_state(states.Idea.awaiting_question)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.message(states.Idea.awaiting_question)
async def handle_question_input(message: Message, state: FSMContext):
    try:
        question = message.text
        if not question or len(question.strip()) < 5:
            await message.answer("Вопрос слишком короткий. Пожалуйста, опишите подробнее:")
            return
        
        await state.update_data(question=question)
        await state.set_state(states.Idea.start)
        
        await message.answer(
            "К какому из ваших проектов относится данный вопрос?",
            reply_markup=await inline_keyboards.get_precise_catalogue(telegram_id=message.from_user.id)
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, произошла ошибка", reply_markup=inline_keyboards.home)
        await state.clear()

@router.callback_query(F.data.startswith("choose_business_"), states.Idea.start)
async def idea_generator_finish(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        question = data.get("question")
        if not question:
            await callback.message.answer("Извините, бот забыл про какой бизнес мы говорили 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            return
        
        business_id = int(callback.data.replace("choose_business_", ""))
        current_business = await get_business(
            telegram_id=callback.from_user.id,
            business_id=business_id
        )
        if not current_business:
            await callback.message.answer("Извините, бот не смог найти ваш бизнес 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            return
        
        await callback.message.answer("Ассистент думает, подождите пожалуйста...")
        response = await post_idea_model(
            telegram_id=callback.from_user.id,
            text=question,
            description=current_business.get("description"),
            business=current_business.get("name"),
        )
        
        logging.info(response)
        
        if not response:
            await callback.message.answer("Модель не смогла дать внятного ответа, попробуйте переформулировать...", reply_markup=inline_keyboards.home)
            return
        
        await callback.message.answer(
            response,
            reply_markup= inline_keyboards.main
        )
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()
#===========================================================================================================================
# Summarise
#===========================================================================================================================


@router.callback_query(F.data == "information_structure")
async def get_information_structure(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "напишите информацию для структурирования боту",
        )
        await state.set_state(states.Summarizer.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.Summarizer.start)
async def summarizer_send_request(message:Message, state:FSMContext):
    try:
        user_question = message.text
        await state.update_data(
            user_question = user_question
        )
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        await message.answer("Я вас понял, дайте секунду сформулировать...")
        result = await post_summarize_model(
            telegram_id = message.from_user.id,
            text = user_question
        )
        if result is None:
            await message.answer(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
        if not isinstance(result, dict):
            await message.answer(
                result,
                reply_markup=inline_keyboards.main
            )
        elif isinstance(result, dict):
            await message.answer(
                result.get("response"),
                reply_markup=inline_keyboards.main
            )
        else:
            logging.info(result)
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await message.answer(
            "Извините, бот немножко устал, попробуйте позже 😢", 
            reply_markup=inline_keyboards.retry_keyboard
        )
        await state.set_state(states.Summarizer.start)


@router.callback_query(F.data == "retry_question", states.Summarizer.start)
async def retry_summarize_question(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Повторяю запрос...")
        state_data = await state.get_data()
        user_question = state_data.get('user_question')
        
        if not user_question:
            await callback.message.answer(
                "Не удалось найти предыдущий вопрос. Пожалуйста, задайте вопрос заново.",
                reply_markup=inline_keyboards.home
            )
            await state.clear()
            return
        await callback.message.edit_text("Повторяю запрос, секунду...")
        result = await post_summarize_model(
            telegram_id=callback.from_user.id,
            text=user_question
        )
        if result is None:
            await callback.message.edit_text(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
            
        if not isinstance(result, dict):
            await callback.message.edit_text(
                result,
                reply_markup=inline_keyboards.main
            )
        else:
            raise Exception("eeror while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)

        await callback.message.edit_text(
            "Снова произошла ошибка. Попробовать еще раз?",
            reply_markup=inline_keyboards.retry_keyboard
        )


#===========================================================================================================================
# Business analytics
#===========================================================================================================================

@router.callback_query(F.data == "business_analysis")
async def get_analyzis_type(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "Какой вид анализа вы хотите провести?",
            reply_markup=inline_keyboards.business_analysis
        )
        await state.set_state(states.Summarizer.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


#==================
# Business analysis
#==================

@router.callback_query(F.data == "swot_start")
async def swot_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "swot")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "bmc_start")
async def bmc_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "bmc")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "cjm_start")
async def cjm_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "cjm")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "vpc_start")
async def vpc_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "vpc")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.callback_query(F.data == "pest_start")
async def pest_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "pest")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



@router.message(states.Analysys.swot)
async def analyzer_send_request(message:Message, state:FSMContext, bot:Bot):
    try:
        user_question = message.text
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        await state.update_data(
            question = user_question
        )
        await message.answer(
            "К какому из ваших проектов относится данный вопрос?",
            reply_markup=await inline_keyboards.get_precise_catalogue(telegram_id=message.from_user.id)
        )
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤔"
        )
        await state.set_state(states.Analysys.cjm)

    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



@router.callback_query(F.data.startswith("choose_business_"), states.Analysys.cjm)
async def business_analysis_finish(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer("Я вас понял, дайте секунду проанализировать...")
        data = await state.get_data()
        analyzys_type = data.get("type")
        if not analyzys_type:
            raise ValueError("No type was saved")

        question = data.get("question")
        if not question:
            raise ValueError("No question was saved")

        business_id = int(callback.data.replace("choose_business_", ""))
        current_business = await get_business(
            telegram_id=callback.from_user.id,
            business_id=business_id
        )
        if not current_business:
            await callback.message.answer("Извините, бот не смог найти ваш бизнес 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            return
        await callback.message.answer("Ассистент думает, подождите пожалуйста...")
        response = await post_analysis_model(
            telegram_id=callback.from_user.id,
            text=question,
            description=current_business.get("description"),
            business=current_business.get("name"),
            analysis_type=analyzys_type,
            offset = 0
        )
        logging.info(response)
        if not response:
            await callback.message.answer("Модель не смогла дать внятного ответа, попробуйте переформулировать...", reply_markup=inline_keyboards.home)
            return
        
        await callback.message.answer(
            response,
            reply_markup= inline_keyboards.main
        )
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message()
async def chat_model_answer(message:Message, state:FSMContext, bot:Bot, threshold = 5):
    try:
        await message.answer("Перенаправляем ваш запрос к нашему чат-ассистенту...")
        question = message.text
        if not question or len(question) < threshold:
            await message.answer("Неизвестная команда 🧐")
            await message.answer("Если вы хотите что-то спросить у чат-бота, раскройте более подробно свой вопрос пожалуйста")
        await state.set_state(states.ChatModelAsk.start)
        await state.update_data(question = question)
        await message.answer(
            "К какому из ваших проектов относится данный вопрос?\n\nЭто нужно нам для более точного понимания ваших потребностей...",
            reply_markup= await inline_keyboards.get_precise_catalogue(telegram_id=message.from_user.id)
        )
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤔"
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.callback_query(F.data.startswith("choose_business_"), states.ChatModelAsk.start)
async def chat_model_finish(callback:CallbackQuery, state:FSMContext):
    try:
        data = await state.get_data()
        question = data.get("question")
        if not question:
            await callback.message.answer("Извините, бот забыл про какой бизнес мы говорили 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            raise ValueError("Error while memorising the question")
        business_id = int(callback.data.strip().split("_")[2])
        current_business = await get_business(
            telegram_id=callback.from_user.id,
            business_id=business_id
        )
        if not current_business:
            await callback.message.answer("Извините, бот не смог найти ваш бизнес 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            raise ValueError("Error while memorising the question")
        await callback.message.answer("Ассистент думает, подождите пожалуйста...")
        response = await post_chat_model(
            telegram_id=callback.from_user.id,
            text = question,
            description = current_business.get("description"),
            business = current_business.get("name"),
        )
        logging.info(response)
        if not response:
            await callback.message.answer("Модель не смогла дать внятного ответа, попробуйте переформулировать...", reply_markup=inline_keyboards.home)
            return
        await callback.message.answer(
            response,
            reply_markup= inline_keyboards.main
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()
