from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from app.requests.get.get_datasets import get_datasets
from app.requests.get.get_distributions import get_distributions
from pprint import pprint


task_choice = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Регрессия", callback_data="task_regression")],
        [InlineKeyboardButton(text="Классификация", callback_data="task_classification")],
        [InlineKeyboardButton(text="Кластеризация", callback_data="task_clusterization")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ]
)

def list_ml_models(data, task):
    keyboard = InlineKeyboardBuilder()
    data = [] if data is None or not data else data
    for model in data:
        keyboard.add(InlineKeyboardButton(text=f"{model.get('name', "Неизвестная модель")}", callback_data=f"MLmodel_{model.get('id')}"))
    keyboard.add(InlineKeyboardButton(text="Создать модель ✨", callback_data=f"create_ML_model_{task}"))
    keyboard.add(InlineKeyboardButton(text="Сгенерировать выборку ✍️", callback_data=f"geterate_sample_{task}"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


def single_model_menu(
    model,
    model_id
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Предсказать", callback_data=f"model_predict_{model_id}"))
    keyboard.add(InlineKeyboardButton(text="Дообучить", callback_data=f"model_fit_{model_id}"))
    keyboard.add(InlineKeyboardButton(text="Обучить заново", callback_data=f"model_refit_{model_id}"))
    keyboard.add(InlineKeyboardButton(text="Редактировать модель", callback_data=f"model_put_{model_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить модель", callback_data=f"model_delete_{model_id}"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


MODEL_TYPES_BY_TASK = {
    'regression': (
        ('linear_regression', 'Linear Regression'),
        ('polinomial_regression', 'Polinomial Regression'),
        ('knn_regression', 'KNN Regression'),
        ('gradient_boosting_regression', 'Gradient Boosting Regression'),
    ),
    'classification': (
        ('logistic_regression', 'Logistic Regression'),
        ('support_vector_machine_classification', 'SVM Classification'),
        ('knn_classification', 'KNN Classification'),
        ('random_forest_classification', 'Random Forest Classification'),
        ('gradient_boosting_classification', 'Gradient Boosting Regression'),
    ),
    'clusterization': (
        ('kmeans_clusterization', 'KMeans clusterization'),
        ('density_clusterization', 'Density clusterization'),
    )
}


def list_ml_algorithms(task):
    keyboard = InlineKeyboardBuilder()
    algorithms = MODEL_TYPES_BY_TASK.get(task, [])
    for model in algorithms:
        keyboard.add(InlineKeyboardButton(text=f"{model[1]}", callback_data=f"create_model_{model[0]}"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return keyboard.adjust(1).as_markup()


def select_target_column(columns):
    keyboard = InlineKeyboardBuilder()
    for col in columns:
        keyboard.add(InlineKeyboardButton(text=col, callback_data=f"select_target_{col}"))
    return keyboard.adjust(1).as_markup()


def confirm(model_id:int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_{model_id}"))
    keyboard.add(InlineKeyboardButton(text="Отклонить", callback_data=f"decline_{model_id}"))
    return keyboard.adjust(1).as_markup()
