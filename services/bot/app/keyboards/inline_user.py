from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from pprint import pprint
from app.requests.get.get_business import get_business, get_user_business
from app.requests.reports.get_report import get_user_report
import logging
from aiogram.fsm.context import FSMContext

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📦 Каталог", callback_data="catalogue")],
        [InlineKeyboardButton(text="📊 Модели юнит-экономика", callback_data="unit_menu_list")],
        [InlineKeyboardButton(text="🤖 ИИ-инструменты", callback_data="ai_menu")],
        [InlineKeyboardButton(text="👤 Аккаунт", callback_data="account_menu")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ]
)



async def get_unit_catalogue(telegram_id, state:FSMContext):
    reports = await get_user_report(
        telegram_id=telegram_id
    )
    await state.update_data(reports = reports)
    keyboard = InlineKeyboardBuilder()
    if reports is None or reports == [] or reports == ():
        keyboard.add(InlineKeyboardButton(text="Создать модель ➕", callback_data="create_report"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        return keyboard.adjust(1).as_markup()
    for report in reports:
        keyboard.add(InlineKeyboardButton(text=f"{report.get('name', 'Модель экономики')}", callback_data=f"report_{report.get('id')}"))
    keyboard.add(InlineKeyboardButton(text="Создать модель ➕", callback_data="create_report"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


async def model_menu(model_id):
    if not model_id:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Пересчитать модель", callback_data=f"recount_model_{model_id}")],
        [InlineKeyboardButton(text="❌ Удалить модель", callback_data=f"delete_model_{model_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

async def email_choice(        
    telegram_id
):
    email_choice = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🙂‍↔️ Нет, спасибо", callback_data="email_deny")],
            [InlineKeyboardButton(text="🧑‍💻 Да, на мою почту", callback_data=f"email_account_{telegram_id}")],
            [InlineKeyboardButton(text="🤖 Да, на укажу почту", callback_data=f"email_custom_{telegram_id}")],
        ]
    )
    return email_choice


async def get_reports(reports):
    keyboard = InlineKeyboardBuilder()
    if reports is None or reports == [] or reports == ():
        keyboard.add(InlineKeyboardButton(text="Создать модель ➕", callback_data="create_report"))
        keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        return keyboard.adjust(1).as_markup()
    for report in reports:
        keyboard.add(InlineKeyboardButton(text=f"{report.get('name', 'Модель экономики')}", callback_data=f"report_{report.get('id')}"))
    keyboard.add(InlineKeyboardButton(text="Создать модель ➕", callback_data="create_report"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


async def get_report_menu(report_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Аналитика", callback_data=f"analise_unit_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать модель 📝", callback_data=f"edit_report_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить модель 🗑️", callback_data=f"delete_report_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="Каталог 📦", callback_data="catalogue"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


async def create_unit_edit_menu(report_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Рассчитать экономику", callback_data=f"count_unit_economics_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="Рассчитать точку безубыточности", callback_data=f"count_unit_bep_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="Когортный анализ", callback_data=f"cohort_analisis_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="Сгенерировать Unit-отчет", callback_data=f"generate_report_unit_{report_id}"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()



account_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👑 Запросить права администратора", callback_data="request_admin")],
        [InlineKeyboardButton(text="❌ Удалить аккаунт", callback_data="delete_account")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

delete_account_confirmation_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="delete_account")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="account_menu")],
    ]
)


async def confirm(        
    object_id:int,
    confirm_callback:str,
    decline_callback:str,
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{confirm_callback + str(object_id)}"))
    keyboard.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"{decline_callback + str(object_id)}"))
    return keyboard.adjust(1).as_markup()


home = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)


home_retry = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать еще", callback_data="retry_send_lawyer")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)


retry_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="retry_question")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ]
        )


restart = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Главное меню", callback_data="restart")],
    ]
)


catalogue = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Персональный юрист", callback_data="personal_lawyer")],
        [InlineKeyboardButton(text="🗣️ Переговорщик", callback_data="conversation")],
        [InlineKeyboardButton(text="💡 Генерация идей", callback_data="idea_generation")],
        [InlineKeyboardButton(text="📊 Бизнес-анализ", callback_data="business_analysis")],
        [InlineKeyboardButton(text="📋 Структурирование информации", callback_data="information_structure")],
        [InlineKeyboardButton(text="🏠 На главную", callback_data="main_menu")]
    ]
)


async def create_catalogue(business_id:int):
    keyboard= InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Персональный юрист", callback_data=f"personal_lawyer_{business_id}")],
            [InlineKeyboardButton(text="🗣️ Переговорщик", callback_data=f"conversation_{business_id}")],
            [InlineKeyboardButton(text="💡 Генерация идей", callback_data=f"idea_generation_{business_id}")],
            [InlineKeyboardButton(text="📊 Бизнес-анализ", callback_data=f"business_analysis_{business_id}")],
            [InlineKeyboardButton(text="📋 Структурирование информации", callback_data=f"information_structure_{business_id}")],
            [InlineKeyboardButton(text="🏠 На главную", callback_data="main_menu")]
        ]
    )
    return keyboard


justice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Юридическая консультация", callback_data="personal_lawyer_start")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalogue")]
    ]
)


idea_generation = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💡 Сгенерировать идеи", callback_data="idea_generate_start")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalogue")]
    ]
)


business_analysis = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📈 SWOT-анализ", callback_data="swot_start")],
        [InlineKeyboardButton(text="🎨 Business Model Canvas", callback_data="bmc_start")],
        [InlineKeyboardButton(text="🛣️ Customer Journey Map", callback_data="cjm_start")],
        [InlineKeyboardButton(text="💎 Value Proposition Canvas", callback_data="vpc_start")],
        [InlineKeyboardButton(text="🌍 PEST-анализ", callback_data="pest_start")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalogue")]
    ]
)

async def give_acess(user_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="✅ Разрешить", callback_data=f"access_give_{user_id}"))
    keyboard.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"access_reject_{user_id}"))
    return keyboard.adjust(1).as_markup()


async def get_business_catalogue(
    telegram_id,
    business_list:list|None = None
):
    keyboard = InlineKeyboardBuilder()
    if business_list is None:
        business_list = await get_user_business(telegram_id=telegram_id)
    if business_list and isinstance(business_list, (list, tuple)):
        for bus in business_list:
            keyboard.add(InlineKeyboardButton(text=f"🏢 {bus.get("name", "business")}", callback_data=f"retrieve_business_{bus.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="➕ Добавить проект", callback_data="create_business"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()



async def get_precise_catalogue(
    telegram_id,
    business_list:list|None = None
):
    keyboard = InlineKeyboardBuilder()
    if business_list is None:
        business_list = await get_user_business(telegram_id=telegram_id)
    if business_list and isinstance(business_list, (list, tuple)):
        for bus in business_list:
            keyboard.add(InlineKeyboardButton(text=f"🏢 {bus.get("name", "business")}", callback_data=f"choose_business_{bus.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


async def get_single_business(
    telegram_id,
    business:dict
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="✏️ Изменить Бизнес", callback_data=f"edit_business_{business.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="🗑️ Удалить Бизнес", callback_data=f"delete_business_{business.get("id")}"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()