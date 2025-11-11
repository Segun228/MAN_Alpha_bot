from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from app.requests.get.get_datasets import get_datasets
from app.requests.get.get_distributions import get_distributions
from pprint import pprint


async def get_dataset_single_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="АБ тесты", callback_data=f"ab_tests_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="ML-алгоритмы", callback_data=f"ml_algorithms_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать", callback_data=f"edit_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"delete_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


async def get_confirm_menu(
    true_callback = "confirm_ztest",
    false_callback = "catalogue",
    dataset_id = None
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Подтвердить", callback_data=true_callback))
    keyboard.add(InlineKeyboardButton(text="Отмена", callback_data=false_callback))
    return keyboard.adjust(1).as_markup()


async def get_dataset_ab_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Указать тестовую и контрольную группы", callback_data=f"set_groups_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Указать α и β", callback_data=f"set_errors_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Критерии", callback_data=f"get_criteria_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Рассчитать N", callback_data=f"count_n_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Рассчитать MDE", callback_data=f"count_mde_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Очистить данные", callback_data=f"clear_dataset_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Повышение точности", callback_data=f"precision_menu_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"dataset_{dataset_id}"))
    return keyboard.adjust(1).as_markup()


async def get_precision_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="CUPED", callback_data=f"cuped_{dataset_id}"))    
    keyboard.add(InlineKeyboardButton(text="CUPAC", callback_data=f"cupac_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"dataset_{dataset_id}"))
    return keyboard.adjust(1).as_markup()


async def get_dataset_ml_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Регрессия", callback_data=f"make_regression_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Классификация", callback_data=f"make_classification_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Кластеризация", callback_data=f"make_clusterization_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"dataset_{dataset_id}"))
    return keyboard.adjust(1).as_markup()


async def get_dataset_criteria_menu(dataset_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Z-test", callback_data=f"ztest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Student t-test", callback_data=f"ttest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="χ² 2 sample Pearson test", callback_data=f"chi2test_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="U - test", callback_data=f"utest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Welch’s t-test", callback_data=f"welchtest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Anderson-Darling test", callback_data=f"andersondarlingtest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Anderson-Darling 2-sample test", callback_data=f"andersondarling2sampletest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Cramer test", callback_data=f"cramertest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="KS two-sample test", callback_data=f"kstest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Shapiro-Wilke test", callback_data=f"shapirowilketest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Lilleforce test", callback_data=f"lilleforcetest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="Bootstrap", callback_data=f"bootstraptest_{dataset_id}"))
    keyboard.add(InlineKeyboardButton(text="ANOVA", callback_data=f"anovatest_{dataset_id}"))
    
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"ab_tests_{dataset_id}"))
    return keyboard.adjust(1).as_markup()