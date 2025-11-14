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

from app.states.states import Send

from aiogram.types import BufferedInputFile

from app.filters.IsAdmin import IsAdmin

from app.requests.user.login import login
from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.user.get_alive import get_alive
from app.requests.user.make_admin import make_admin

from app.kafka.utils import build_log_message


import re
from typing import Optional

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


@router.message(Command("start"))
async def cmd_start(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command", 
        payload="start"
    )
    welcome_text = """
    *🚀 Добро пожаловать в Business Analyst AI!*

    Я ваш персональный AI-помощник для развития бизнеса. Помогаю анализировать данные, генерировать идеи и находить пути для роста.

    *🎯 Что я могу для вас сделать:*

    • *📊 Проанализировать* ваши бизнес-метрики
    • *💡 Сгенерировать* новые идеи для развития  
    • *📝 Структурировать* отчеты и документы
    • *🔍 Выявить* слабые места и возможности
    • *🎯 Предложить* конкретные шаги для улучшений

    *📋 Доступные разделы:*
    - Бизнес-аналитика
    - Генерация идей  
    - Суммаризация данных
    - SWOT-анализ
    - Персональные рекомендации

    *🔍 Используйте команды:*
    /help - подробная инструкция
    /info - о боте и возможностях  
    /contacts - связь с поддержкой

    *Выберите раздел ниже чтобы начать работу! 👇*
    """
    welcome_text = escape_markdown_v2(
        welcome_text
    )
    
    await message.reply(
        text=welcome_text,
        reply_markup=inline_keyboards.main_menu,#TODO
        parse_mode='MarkdownV2'
    )


@router.callback_query(F.data == "restart")
async def callback_start_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    data = await login(telegram_id=callback.from_user.id)
    if data is None:
        logging.error("Error while logging in")
        await callback.message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    
    await state.update_data(telegram_id=data.get("telegram_id"))
    reply_string = escape_markdown_v2(
        "🎯 *Что я могу для вас сделать:*\n\n"
        "• *📊 Проанализировать* ваши бизнес-метрики\n"
        "• *💡 Сгенерировать* новые идеи для развития\n"  
        "• *📝 Структурировать* отчеты и документы\n"
        "• *🔍 Выявить* слабые места и возможности\n"
        "• *🎯 Предложить* конкретные шаги для улучшений\n\n"
        "Выберите раздел ниже чтобы начать работу! 👇"
    )
    await callback.message.reply("Приветствую! 👋")
    await callback.message.answer("Я ваш персональный AI-помощник для развития бизнеса!")
    await callback.message.answer(
        reply_string,
        parse_mode='MarkdownV2',
        reply_markup=inline_keyboards.main_menu  #TODO
    )
    
    await callback.answer()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="restart"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command", 
        source="command",
        payload="help"
    )
    
    help_text = """
        🤖 *Бизнес-Аналитик AI* - ваш персональный помощник в развитии бизнеса!

        Вы можете просто общаться с ним как с чат-ботом, просто напишите в чат ваш вопрос

        *🎯 Дополнительные возможности:*

        • *Анализ бизнес-метрик* - оценка ключевых показателей
        • *Генерация идей* - креативные решения для роста  
        • *Суммаризация данных* - структурирование отчетов и диалогов
        • *SWOT-анализ* - выявление сильных и слабых сторон
        • *Рекомендации* - персонализированные советы по развитию

        *📊 Доступные инструменты:*
        - Анализ финансовых показателей
        - Маркетинговая аналитика  
        - Оптимизация бизнес-процессов
        - Прогнозирование трендов
        - Сравнение с конкурентами

        *💡 Как работать с ботом:*
        1. Выберите интересующий раздел в меню
        2. Следуйте инструкциям бота
        3. Получайте структурированные insights

        Начните с команды /start для доступа ко всем функциям!
    """
    help_text = escape_markdown_v2(
        help_text
    )
    await message.reply(
        text=help_text,
        reply_markup=inline_keyboards.home,
        parse_mode='MarkdownV2'
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
    *📞 Контакты поддержки*

    *🤝 Реклама и сотрудничество:*
    @dianabol_metandienon_enjoyer

    *🤝 Техническая поддержка:*
    @mattwix

    *🤝 Проблеммы с ИИ:*
    @andy_andy13

    *⏰ Время работы поддержки:*
    Пн-Пт: 8:00 - 18:00 (МСК)
    Сб-Вс: по запросу

    *🚀 Мы поможем:*
    • Согласовать рекламу и сотрудничество
    • Настроить работу с ботом
    • Ответим на вопросы по аналитике
    • Примем предложения по улучшению
    • Решим технические проблемы

    *📧 Альтернативные способы связи:*
    Для срочных вопросов используйте Telegram
    """
    contacts_text = escape_markdown_v2(
        contacts_text
    )
    await message.reply(
        text=contacts_text,
        reply_markup=inline_keyboards.home,
        parse_mode='MarkdownV2'
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
        *🏢 О Business Analyst AI*

        *🎯 Наша миссия:*
        Помогать предпринимателям принимать взвешенные бизнес-решения на основе данных и AI-аналитики.

        *🔍 Что мы делаем:*
        • Анализируем ваши бизнес-показатели
        • Структурируем разрозненные данные  
        • Генерируем практические идеи для роста
        • Выявляем скрытые возможности
        • Предлагаем конкретные шаги для улучшения

        *📈 Преимущества:*
        ✅ *Простота* - интуитивный интерфейс
        ✅ *Скорость* - мгновенная аналитика  
        ✅ *Точность* - на основе современных AI-моделей
        ✅ *Конфиденциальность* - ваши данные в безопасности

        *🛠 Технологии:*
        • Современные языковые модели (LLM)
        • Статистический анализ данных
        • Машинное обучение для прогнозирования
        • Эмбеддинги для работы с документами

        *💼 Для кого наш бот:*
        • Малый и средний бизнес
        • Стартапы и предприниматели  
        • Фрилансеры и самозанятые
        • Все, кто хочет развивать свой бизнес

        *Начните улучшать свой бизнес уже сегодня! 🚀*
    """
    info_text = escape_markdown_v2(
        info_text
    )
    await message.reply(
        text=info_text,
        reply_markup=inline_keyboards.home,
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "contacts")
async def contacts_callback(callback: CallbackQuery):
    contacts_text = """
    *📞 Контакты поддержки*

    *🤝 Реклама и сотрудничество:*
    @dianabol_metandienon_enjoyer

    *🤝 Техническая поддержка:*
    @mattwix

    *🤝 Проблеммы с ИИ:*
    @andy_andy13

    *⏰ Время работы поддержки:*
    Пн-Пт: 8:00 - 18:00 (МСК)
    Сб-Вс: по запросу

    *🚀 Мы поможем:*
    • Согласовать рекламу и сотрудничество
    • Настроить работу с ботом
    • Ответим на вопросы по аналитике
    • Примем предложения по улучшению
    • Решим технические проблемы

    *📧 Альтернативные способы связи:*
    Для срочных вопросов используйте Telegram
    """
    contacts_text = escape_markdown_v2(
        contacts_text
    )
    await callback.message.reply(
        text=contacts_text,
        reply_markup=inline_keyboards.home,
        parse_mode='MarkdownV2'
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
# Каталог
#===========================================================================================================================


@router.callback_query(F.data == "catalogue")
async def get_catalogue_menu(callaback:CallbackQuery):
    await callaback.message.answer(
        "Вы можете задать специализированные вопросы:",
        reply_markup=inline_keyboards.catalogue
    )