from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from app.requests.get.get_datasets import get_datasets
from app.requests.get.get_distributions import get_distributions
from pprint import pprint

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Каталог 📦", callback_data="catalogue")],
        [InlineKeyboardButton(text="👤 Аккаунт", callback_data="account_menu")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ]
)

account_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Админ ⚙️", callback_data="admin_menu")],
        [InlineKeyboardButton(text="Запросить права администратора 👑", callback_data="request_admin")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

delete_account_confirmation_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="delete_account")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="account_menu")],
    ]
)



home = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

restart = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Главное меню", callback_data="restart")],
    ]
)


catalogue = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=" Каталог", callback_data="catalogue")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

catalogue_choice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Распределения", callback_data="distributions")],
        [InlineKeyboardButton(text="Датасеты", callback_data="datasets")],
        [InlineKeyboardButton(text="ML модели", callback_data="ml_models")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

no_posts = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=" Создать модель ✍️", callback_data="catalogue")],
        [InlineKeyboardButton(text=" Каталог 📖", callback_data="catalogue")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)



async def get_datasets_catalogue(telegram_id, datasets = None):
    if datasets is None:
        datasets = await get_datasets(telegram_id=telegram_id)
        print(datasets)
    keyboard = InlineKeyboardBuilder()
    pprint(datasets)
    if datasets and datasets is not None:
        for dataset in datasets:
            keyboard.add(InlineKeyboardButton(text=f"{dataset.get('name', dataset.get("columns", "Безымянный датасет"))}", callback_data=f"dataset_{dataset.get('id')}"))
    keyboard.add(InlineKeyboardButton(text="Добавить датасет ✨", callback_data="create_dataset"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()

async def get_distributions_catalogue(telegram_id, distributions = None):
    if distributions is None:
        distributions = await get_distributions(telegram_id=telegram_id)
    pprint(distributions)
    keyboard = InlineKeyboardBuilder()
    if distributions and distributions is not None:
        for distribution in distributions:
            keyboard.add(InlineKeyboardButton(text=f"{distribution.get('name')}", callback_data=f"distribution_{distribution.get('id')}"))
    keyboard.add(InlineKeyboardButton(text="Добавить распределение ✨", callback_data="create_distribution"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()

async def give_acess(user_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Разрешить ✅", callback_data=f"access_give_{user_id}"))
    keyboard.add(InlineKeyboardButton(text="Отклонить ❌", callback_data=f"access_reject_{user_id}"))
    return keyboard.adjust(1).as_markup()


async def get_distribution_single_menu(distribution_id, telegram_id, distribution):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="График", callback_data=f"get_plot_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Вероятность", callback_data=f"get_probability_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Интервал", callback_data=f"get_interval_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Квантиль", callback_data=f"get_quantile_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Персентиль", callback_data=f"get_percentile_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Выборка", callback_data=f"get_sample_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать", callback_data=f"edit_distribution_{distribution_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_distribution_{distribution_id}"))
    return keyboard.adjust(1).as_markup()



async def get_dataset_single_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="АБ тесты", callback_data=f"ab_tests_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="ML-алгоритмы", callback_data=f"ml_algorithms_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Получить файл", callback_data=f"datasetfile_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать", callback_data=f"edit_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="datasets"))
    return keyboard.adjust(1).as_markup()


async def get_dataset_ab_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Получить файл", callback_data=f"datasetfile_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="АБ тесты", callback_data=f"ab_tests_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="ML-алгоритмы", callback_data=f"ml_algorithms_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать", callback_data=f"edit_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_dataset_{dataset_id}"))
    return keyboard.adjust(1).as_markup()


async def get_dataset_ml_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Получить файл", callback_data=f"datasetfile_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="АБ тесты", callback_data=f"ab_tests_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="ML-алгоритмы", callback_data=f"ml_algorithms_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать", callback_data=f"edit_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_dataset_{dataset_id}"))
    return keyboard.adjust(1).as_markup()

DISTRIBUTION_CHOICES = [
    ("normal", "Normal (Нормальное)"),
    ("binomial", "Binomial (Биномиальное)"),
    ("poisson", "Poisson (Пуассон)"),
    ("uniform", "Uniform (Равномерное)"),
    ("exponential", "Exponential (Экспоненциальное)"),
    ("beta", "Beta (Бета)"),
    ("gamma", "Gamma (Гамма)"),
    ("lognormal", "Log-normal (Лог-нормальное)"),
    ("chi2", "Chi-squared (Хи-квадрат)"),
    ("t", "Student t (Стьюдента)"),
    ("f", "F-distribution (Фишера)"),
    ("geometric", "Geometric (Геометрическое)"),
    ("hypergeom", "Hypergeometric (Гипергеометрическое)"),
    ("negative_binomial", "Negative Binomial (Отрицательно биномиальное)"),
]

async def choose_distribution_type():
    keyboard = InlineKeyboardBuilder()
    for typum in DISTRIBUTION_CHOICES:
        keyboard.add(InlineKeyboardButton(text=f"{typum[1]}", callback_data=typum[0]))
    return keyboard.adjust(1).as_markup()