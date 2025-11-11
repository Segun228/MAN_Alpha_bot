from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Union, List
import pandas as pd

def create_reply_column_keyboard_group(columns: Union[pd.DataFrame, List[str], tuple[str]]) -> ReplyKeyboardMarkup:
    if isinstance(columns, pd.DataFrame):
        columns = columns.columns.tolist()

    buttons = [KeyboardButton(text=col) for col in columns]

    keyboard_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]


    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard