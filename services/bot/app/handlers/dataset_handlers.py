from app.handlers.router import dataset_router as router
import logging
import re
import zipfile
import io
import json
import re
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

from app.keyboards import inline_user as inline_user_keyboards

from app.keyboards import inline_dataset as inline_keyboards

from app.states.states import Errors, Groups, Confirm, Bootstrap, Cuped, Cupac

import pandas as pd
import numpy as np


from app.keyboards.inline_user import  get_distributions_catalogue

from app.filters.IsAdmin import IsAdmin

from app.requests.user.login import login
from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.user.get_alive import get_alive
from app.requests.user.make_admin import make_admin

from app.kafka.utils import build_log_message

from app.requests.get.get_datasets import get_datasets, retrieve_dataset
from app.requests.get.get_distributions import get_distributions, retrieve_distribution

from app.requests.post.post_dataset import post_dataset
from app.requests.post.post_distribution import post_distribution

from app.requests.put.put_dataset import put_dataset
from app.requests.put.put_distribution import put_distribution

from app.requests.delete.delete_dataset import delete_dataset
from app.requests.delete.deleteDistribution import delete_distribution

from app.requests.dataset.patch_errors.patch_errors import patch_errors
from app.requests.dataset.patch_categories.patch_groups import set_groups

from app.keyboards.reply_dataset import create_reply_column_keyboard_group
from app.states.states import SampleSize


from app.requests.dataset import stats_handlers
from math import floor, ceil

def escape_md(text: str) -> str:
    """Экранирование специальных символов для MarkdownV2"""
    if not text:
        return ""
    
    escape_chars = '_*[]()~`>#+-=|{}.!'
    result = []
    for char in str(text):
        if char in escape_chars:
            result.append(f'\\{char}')
        else:
            result.append(char)
    return ''.join(result)

#===========================================================================================================================
# Меню
#===========================================================================================================================

def escape_md_v2(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

@router.callback_query(F.data.startswith("ab_tests"))
async def get_datasets_ab_test_menu(callback: CallbackQuery):
    try:
        dataset_id = int(callback.data.split("_")[2])
        await callback.message.answer("Выберите необходимый инструмент", reply_markup=await inline_keyboards.get_dataset_ab_menu(dataset_id=dataset_id))
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await callback.message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.callback_query(F.data.startswith("ml_algorithms"))
async def get_datasets_ml_algo_menu(callback: CallbackQuery):
    try:
        dataset_id = int(callback.data.split("_")[2])
        await callback.message.answer("Выберите необходимый алгоритм", reply_markup=await inline_keyboards.get_dataset_ml_menu(dataset_id=dataset_id))
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await callback.message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("get_criteria_"))
async def get_datasets_ab_criteria_menu(callback: CallbackQuery):
    try:
        dataset_id = int(callback.data.split("_")[2])
        await callback.message.answer("Выберите необходимый алгоритм", reply_markup=await inline_keyboards.get_dataset_criteria_menu(dataset_id=dataset_id))
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await callback.message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.callback_query(F.data.startswith("precision_menu_"))
async def get_datasets_precision_criteria_menu(callback: CallbackQuery):
    try:
        dataset_id = int(callback.data.split("_")[2])
        await callback.message.answer("Выберите необходимый метод повышения точноти", reply_markup=await inline_keyboards.get_precision_menu(dataset_id=dataset_id))
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await callback.message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# Установка альфа и бета
#===========================================================================================================================

@router.callback_query(F.data.startswith("set_errors_"))
async def set_errors(callback: CallbackQuery, state:FSMContext):
    try:
        dataset_id = int(callback.data.split("_")[2])
        await callback.message.answer("Выберите ошибку первого рода")
        await state.set_state(Errors.handle_errors)
        await state.update_data(id = dataset_id)
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await callback.message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.message(Errors.handle_errors)
async def alpha_errors(message:Message, state:FSMContext):
    try:
        alpha = float(message.text.strip())
        await state.update_data(alpha = alpha)
        await message.answer("Выберите ошибку второго рода")
        await state.set_state(Errors.alpha)
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.message(Errors.alpha)
async def beta_errors(message:Message, state:FSMContext):
    try:
        beta = float(message.text.strip())
        data = await state.get_data()
        dataset_id = data.get("id")
        alpha = data.get("alpha")
        response = await patch_errors(dataset_id = dataset_id, alpha = alpha, beta = beta, telegram_id=message.from_user.id)
        if response:
            await message.answer("Данные успешно обновлены!",reply_markup=await inline_keyboards.get_dataset_ab_menu(dataset_id=dataset_id))
        await state.set_state(Errors.alpha)
        await state.clear()
    except Exception as e:
        logging.error("An error occured")
        logging.exception(e)
        await message.answer("Извините, возникла ошибка. Попробуйте позже(", reply_markup=inline_user_keyboards.catalogue)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

#===========================================================================================================================
# Установка теста и контроля
#===========================================================================================================================

@router.callback_query(F.data.startswith("set_groups"))
async def set_groups_start(callback: CallbackQuery, state:FSMContext):
    try:
        dataset_id = callback.data.split("_")[2]
        await state.set_state(Groups.handle)
        await state.update_data(id = dataset_id)
        dataset = await retrieve_dataset(
            telegram_id=callback.from_user.id,
            dataset_id=int(dataset_id)
        )
        if dataset is None:
            raise ValueError("Error while getting dataset info from the server")
        await state.update_data(
            columns = dataset.get("columns")
        )
        await callback.message.answer("Выберите тестовую группу", reply_markup=create_reply_column_keyboard_group(columns=dataset.get("columns")))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, не удалось установить группы, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.message(Groups.handle)
async def set_control_group(message:Message, state:FSMContext):
    try:
        test_group = message.text.strip()
        await state.set_state(Groups.controle)
        await state.update_data(test = test_group)
        data = await state.get_data()
        columns = data.get("columns")
        await message.answer("Выберите контрольную группу", reply_markup=create_reply_column_keyboard_group(columns=columns))
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, не удалось установить группы, попробуйте позже")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.message(Groups.controle)
async def set_end_group(message:Message, state:FSMContext):
    try:
        controle_group = message.text.strip()
        data = await state.get_data()
        test = data.get("test")
        dataset_id = data.get("id")
        answer = await set_groups(
            telegram_id = message.from_user.id,
            dataset_id = dataset_id,
            test = test,
            control = controle_group
        )
        if answer:
            await message.answer("Группы успешно выбраны!", reply_markup=await inline_keyboards.get_dataset_ab_menu(dataset_id=dataset_id))
            current_dataset = await retrieve_dataset(telegram_id=message.from_user.id, dataset_id=dataset_id)
            if current_dataset is None:
                await message.answer("Извините, тут пока пусто, возвращаейтесь позже!", reply_markup= await get_distributions_catalogue(telegram_id=message.from_user.id))
                return
            data = current_dataset

            name = escape_md(data['name'])
            alpha = escape_md(str(data['alpha']))
            beta = escape_md(str(data['beta']))
            test_val = escape_md(str(data['test']) or "Not set yet")
            control_val = escape_md(str(data['control']) or "Not set yet")
            length = escape_md(str(data['length']) or "Not set yet")


            params = data['columns']
            param_string = "\n"
            for nam in params:
                escaped_nam = escape_md(nam)
                param_string += f"*{escaped_nam}*\n"
            param_string += "\n"

            msg = (
                f"*Name:* {name}\n\n"
                f"*Columns:* {param_string}"
                f"*Alpha:* {alpha}\n"
                f"*Beta:* {beta}\n\n"
                f"*Test group:* {test_val}\n"
                f"*Controle group:* {control_val}\n\n"
                f"*Final length:* {length}\n"
            )
            await message.answer(msg, parse_mode="MarkdownV2", reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id = dataset_id))
        
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, не удалось установить группы, попробуйте позже")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
#===========================================================================================================================
# рассчет N
#===========================================================================================================================

@router.callback_query(F.data.startswith("count_n"))
async def count_n_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[2]
        await state.update_data(id = dataset_id)
        await callback.message.answer("Введите, какой минимальный эффект вы хотите обнаружить (в единицах измерения целевой метрики)")
        await state.set_state(SampleSize.mde)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

def format_mde_message(result):
    from math import ceil

    MDE = escape_md_v2(str(result['MDE']))
    MDE_pct = escape_md_v2(f"{result['MDE_%']:.2f}")
    test_size = escape_md_v2(str(ceil(result['test_size'])))
    control_size = escape_md_v2(str(ceil(result['control_size'])))
    n_total = escape_md_v2(str(ceil(result['n_total'])))
    text = (
        f"*Расчёт MDE и размеров выборки*\n\n"
        f"📊 *Минимальная детектируемая разница \(MDE\)*:\n"
        f"`{MDE}` \({MDE_pct}%\)\n\n"
        f"👥 *Размеры выборок*\n"
        f"Тестовая группа: `{test_size}`\n"
        f"Контрольная группа: `{control_size}`\n"
        f"Общее количество: `{round(float(control_size))+round(float(test_size))}`"
    )
    return text

@router.message(SampleSize.mde)
async def count_n_end(message: Message, state: FSMContext):
    try:
        message.answer("Запускаю рассчет...")
        mde = float(message.text)
        if not mde:
            raise ValueError("Invalid MDE given")
        data = await state.get_data()
        dataset_id = data.get("id")
        await message.answer("Запускаю рассчеты...")

        response = await stats_handlers.count_n(
            telegram_id=message.from_user.id,
            id=dataset_id,
            mde=mde
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)


        await message.answer(
            format_mde_message(result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()

    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

#===========================================================================================================================
# рассчет MDE
#===========================================================================================================================

@router.callback_query(F.data.startswith("count_mde"))
async def count_mde_start(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        await state.clear()
        dataset_id = callback.data.split("_")[2]
        await callback.message.answer("Уже считаю, подождите немного...")
        response = await stats_handlers.count_n(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_mde_message(result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
#===========================================================================================================================
# Z-test
#===========================================================================================================================

def format_test_message(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        z = result.get('z', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты Z\-теста*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 Z\-статистика:* `{z:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("ztest_"))
async def ztest_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Z-тест накладывает на данные ограничения")
        await callback.message.answer("Для корректности теста необходимо, чтобы при рассчете выборка была репрезентативна, а также дисперсия ген. совокупности совпадала с выборочной (особенности программного рассчета)")
        await callback.message.answer("При N<30 данные должны быть нормальными")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_ztest",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.callback_query(F.data.startswith("confirm_ztest"))
async def ztest_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.z_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")
        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# T-test
#===========================================================================================================================

def format_test_message_ttest(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        t = result.get('z', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты T\-теста*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 T\-статистика:* `{t:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise



@router.callback_query(F.data.startswith("ttest_"))
async def ttest_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("T-тест накладывает на данные ограничения")
        await callback.message.answer("Для корректности теста необходимо, чтобы при рассчете выборки были независимы")
        await callback.message.answer("При N<30 данные должны быть нормальными")
        await callback.message.answer("Если дисперсии теста и контроля значительно различаются, вам следует использовать тест Уэлча")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_ttest",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_ttest"))
async def ttest_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.t_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_ttest(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# chisquare-test
#===========================================================================================================================

def format_test_message_shisquare(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        chi2_stat = result.get('chi2_stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты Chi2\-теста*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 Хи\-квадрат\-статистика:* `{chi2_stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("chi2test_"))
async def chi2test_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Тест хи-увадрат накладывает на данные ограничения")
        await callback.message.answer("Данные должны либо быть категориальными, либо искомая метрика должна быть метрикой пропорции")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_chi2test",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.callback_query(F.data.startswith("confirm_chi2test"))
async def confirm_chi2_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.chi2_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_shisquare(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# U-test
#===========================================================================================================================

def format_test_message_U(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Манна\-Уитни*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 U\-статистика:* `{stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("utest_"))
async def utest_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Критерий Манна-Уитни - непараметрический тест, не требует нормальности")
        await callback.message.answer("Данные должны быть порядковыми или ранговыми, независимыми")
        await callback.message.answer("Дисперсии и формы распределений не должны сильно различаться")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_utest",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_utest"))
async def confirm_u_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.u_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_U(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
#===========================================================================================================================
# Welch`s test
#===========================================================================================================================

def format_test_message_welch(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Уэлча*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 T\-статистика:* `{stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("welchtest_"))
async def welchtest_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Тест Уелча - параметрический тест")
        await callback.message.answer("Данные должны быть порядковыми или ранговыми, независимыми")
        await callback.message.answer("Дисперсии могут быть не равны")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_welch",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_welch"))
async def confirm_welch_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.welch_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_welch(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# Anderson-Darling`s test
#===========================================================================================================================

def format_test_message_ad(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)
        effect_control = result.get('effect_control', 0.0)
        control_stat = result.get('control_stat', 0.0)
        control_p = result.get('control_p', 1.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Андерсона\-Дарлинга*\n"
            f"Были проверены обе группы\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"Нулевая гипотеза: данные соответствуют нормальному распределению\n\n"

            f"*🧪 Статистика тестовой группы:* `{stat:.5f}`\n"
            f"*📉 P\-значение тестовой группы:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается. Данные не нормальны" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается. Данные нормальны"}`\n\n"

            f"*🧪 Статистика контрольной группы:* `{control_stat:.5f}`\n"
            f"*📉 P\-значение контрольной группы:* `{control_p:.5f}`\n\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается. Данные не нормальны" if int(effect_control)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается. Данные нормальны"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("andersondarlingtest_"))
async def andersondarlingtest_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Тест Андерсона-Дарлинга - непараметрический тест для проверки соответствия распределению")
        await callback.message.answer("Тест чувствителен к выбросам, попробуйте также тест Шапиро-Уилка")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_ad",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

@router.callback_query(F.data.startswith("confirm_ad"))
async def confirm_ad_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.ad_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_ad(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

#===========================================================================================================================
# Cramer`s test
#===========================================================================================================================


def format_test_message_cr(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Крамера\-фон\-Мизеса*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 Статистика:* `{stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise



@router.callback_query(F.data.startswith("cramertest_"))
async def cramer_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Тест Крамера-фон-Мизеса - непараметрический тест для проверки соответствия распределению, в данном случае проверяет нулевую гипотезу о том что обе выборки пришли из одного и того де распределения")
        await callback.message.answer("Тест требует интегрируемость по Риману, функция распредеелния должна быть непрерывной")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_cramer",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_cramer"))
async def confirm_cramer_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.cramer_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_cr(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
#===========================================================================================================================
# 2 sample Anderson-Darling`s test
#===========================================================================================================================


def format_test_message_ad2(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Андерсона\-Дарлинга*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 Статистика:* `{stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise



@router.callback_query(F.data.startswith("andersondarling2sampletest_"))
async def ad2_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Двувыборочный тест Андерсона-Дарлинга - непараметрический тест для проверки соответствия распределению, в данном случае проверяет нулевую гипотезу о том что обе выборки пришли из одного и того де распределения")
        await callback.message.answer("Усиленная версия теста Крамера-фон-Мизеса")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_ad2",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_ad2"))
async def confirm_ad2_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.cramer_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_cr(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

#===========================================================================================================================
# 2 sample Kolmogorov-Smirnov`s test
#===========================================================================================================================


def format_test_message_ks(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Колмогорова\-Смирнова*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 D\-статистика:* `{stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise



@router.callback_query(F.data.startswith("kstest_"))
async def ks_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Двувыборочный тест Колмогорова-Смирнова - непараметрический тест для проверки соответствия распределению, в данном случае проверяет нулевую гипотезу о том что обе выборки пришли из одного и того де распределения")
        await callback.message.answer("Может быть слабым в хвостах. В таком случае результат может быть завышенным. Попробуйте также тесты Лиллефорса, Крамера-фон-Мизеса и Андерсона-Дарлинга")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_ks",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_ks"))
async def confirm_ks_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.ks_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_ks(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# Shapiro-Wilk`s test
#===========================================================================================================================

def format_test_message_sw(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)
        effect_control = result.get('effect_control', 0.0)
        control_stat = result.get('control_stat', 0.0)
        control_p = result.get('control_p', 1.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Шапиро\-Уилка*\n"
            f"Были проверены обе группы\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"Нулевая гипотеза: данные соответствуют нормальному распределению\n\n"

            f"*🧪 Статистика тестовой группы:* `{stat:.5f}`\n"
            f"*📉 P\-значение тестовой группы:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается. Данные не нормальны" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается. Данные нормальны"}`\n\n"

            f"*🧪 Статистика контрольной группы:* `{control_stat:.5f}`\n"
            f"*📉 P\-значение контрольной группы:* `{control_p:.5f}`\n\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается. Данные не нормальны" if int(effect_control)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается. Данные нормальны"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("shapirowilketest_"))
async def shapiro_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Тест Шапиро-Уилка - параметрический ранговый тест для проверки нормальности")
        await callback.message.answer("Тест робастен к выбросам, обладает высокой мощностью")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_sw",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_sw"))
async def confirm_sw_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.sw_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_sw(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# Lilleforce`s test
#===========================================================================================================================

def format_test_message_ll(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)
        effect_control = result.get('effect_control', 0.0)
        control_stat = result.get('control_stat', 0.0)
        control_p = result.get('control_p', 1.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты теста Лиллефорса*\n"
            f"Были проверены обе группы\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"Нулевая гипотеза: данные соответствуют нормальному распределению\n\n"

            f"*🧪 Статистика тестовой группы:* `{stat:.5f}`\n"
            f"*📉 P\-значение тестовой группы:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается. Данные не нормальны" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается. Данные нормальны"}`\n\n"

            f"*🧪 Статистика контрольной группы:* `{control_stat:.5f}`\n"
            f"*📉 P\-значение контрольной группы:* `{control_p:.5f}`\n\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается. Данные не нормальны" if int(effect_control)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается. Данные нормальны"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("lilleforcetest_"))
async def lilleforce_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Тест Лиллефорса - усиленный тест Колмогорова-Смрнова")
        await callback.message.answer("В тесте не используются истинные параметры распределений")
        await callback.message.answer("Тест не робастен к выбросам, в таком случае попробуйте интегральные признаки, или тест Шапиро-Уилка")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_ll",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )



@router.callback_query(F.data.startswith("confirm_ll"))
async def confirm_ll_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.ll_test(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_ll(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

#===========================================================================================================================
# Bootstrap
#===========================================================================================================================

def format_test_message_bootstrap(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')
        ci = result.get('ci', '?')
        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        t = result.get('z', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')
        iterations = result.get('iterations', '10000')
        text = (
            f"*📊 Результаты бутстрепа*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🚴 Итерации:* `{iterations}`\n"
            f"*🧪 Доверительный интервал:* от `{ci[0]:.5f}` до `{ci[1]:.5f}`\n"
            f"*📐 Эффект:* `{"Ноль не принадлежит CI. Найдено статистически значимое различие. Нулевая гипотеза отвергается" if effect==True else "Ноль принадлежит CI. Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("bootstraptest_"))
async def bootstrap_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("Бутстреп имеет ограничения")
        await callback.message.answer("Для корректности теста необходимо, чтобы при рассчете выборки были независимымы и репрезентативными")
        await callback.message.answer("Это довольно дорогая операция, так что время ожидания может быть дольше чем обычно")
        await callback.message.answer("По умолчанию количество итераций семплирования равно 10000,вы можете увеличить это число, но учтите, что сервер может не справиться. Вы хотите ввести собственное число итераций?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "enter_number_{dataset_id}",
            false_callback = f"confirm_bootstrap_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_bootstrap"))
async def bootstrap_short_end(callback: CallbackQuery, state:FSMContext):
    try:
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.bootstrap(
            telegram_id=callback.from_user.id,
            id=dataset_id,
            iterations = 10000
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await callback.message.answer(
            format_test_message_bootstrap(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("enter_number_"))
async def bootstrap_select_number(callback: CallbackQuery, state:FSMContext):
    await callback.message.answer("Введите желаемое число итераций для бутстрепа (не рекомендуем брать меньше 10000)")
    await state.set_state(Bootstrap.iterations)


@router.message(Bootstrap.iterations)
async def long_bootstrap_finish(message:Message, state:FSMContext):
    try:
        iterations = int(message.text)
        if not iterations:
            iterations = 10000
            message.answer("Извините, не удалось установить кастомное значение, возвращаю дефолтные 10000")
        data = await state.get_data()
        dataset_id = data.get("id")
        await message.answer("Запускаю рассчет...")
        response = await stats_handlers.bootstrap(
            telegram_id=message.from_user.id,
            id=dataset_id,
            iterations = iterations
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")

        result = response if isinstance(response, dict) else json.loads(response.data)

        await message.answer(
            format_test_message_bootstrap(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )

#===========================================================================================================================
# ANOVA
#===========================================================================================================================

def format_test_message_anova(response):
    try:
        result = response
        if type(result) is json or type(result) is str:
            result = json.loads(result)
        n1 = result.get('n1', '?')
        n2 = result.get('n2', '?')

        mean_control = result.get('mean_control', 0.0)
        mean_test = result.get('mean_test', 0.0)

        var_control = result.get('var_control', 0.0)
        var_test = result.get('var_test', 0.0)

        stat = result.get('stat', 0.0)
        p = result.get('p', 1.0)
        effect = result.get('effect', 0.0)

        pearson = result.get('pearson', 0.0)
        pearson_p = result.get('pearson_p', 1.0)

        spearman = result.get('spearman', 0.0)
        spearman_p = result.get('spearman_p', 1.0)

        warning = result.get('warning', '—')

        text = (
            f"*📊 Результаты ANOVA*\n\n"
            f"*👥 Размеры групп:*\n"
            f"Контроль: `{escape_md_v2(n1)}`\n"
            f"Тест: `{escape_md_v2(n2)}`\n\n"

            f"*📈 Средние значения:*\n"
            f"Контроль: `{mean_control:.2f}`\n"
            f"Тест: `{mean_test:.2f}`\n\n"

            f"*📊 Дисперсии:*\n"
            f"Контроль: `{var_control:.2f}`\n"
            f"Тест: `{var_test:.2f}`\n\n"

            f"*🧪 F\-статистика:* `{stat:.5f}`\n"
            f"*📉 P\-значение:* `{p:.5f}`\n"
            f"*📐 Эффект:* `{"Найдено статистически значимое различие. Нулевая гипотеза отвергается" if int(effect)==1 else "Статистически значимого различия не найдено. Нулевая гипотеза не отвергается"}`\n\n"

            f"*📉 Корреляции:*\n"
            f"Пирсон: `{pearson:.3f}` \(p\-value \= `{pearson_p:.5f}`\)\n"
            f"Спирмен: `{spearman:.3f}` \(p\-value \= `{spearman_p:.5f}`\)\n\n"

            f"*⚠️ Предупреждение:*\n"
            f"{escape_md_v2(warning)}"
        )
        return text
    except Exception as e:
        logging.error(e)
        raise


@router.callback_query(F.data.startswith("anovatest_"))
async def anova_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("ANOVA - непараметрический тест, сравнивает средние посредством сравнения дисперсий")
        await callback.message.answer("Данные должны быть независимыми, дисперсии гомогенными")
        await callback.message.answer("В тест встроен анализ дисперсий посредством теста Левана, в случае гетерогенности дисперсий вы получите соответствующее предупреждение")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = "confirm_anova",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("confirm_anova"))
async def confirm_confirm_anova_end(callback: CallbackQuery, state:FSMContext):
    try:
        callback.message.answer("Запускаю рассчет...")
        data = await state.get_data()
        dataset_id = data.get("id")
        response = await stats_handlers.anova(
            telegram_id=callback.from_user.id,
            id=dataset_id,
        )
        if not response:
            logging.error(response)
            raise ValueError("An error occurred during calculation")
        result = response if isinstance(response, dict) else json.loads(response.data)
        await callback.message.answer(
            format_test_message_anova(response = result),
            parse_mode="MarkdownV2",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# CUPED
#===========================================================================================================================


@router.callback_query(F.data.startswith("cuped_"))
async def cuped_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("CUPED - метод повышения точности, базируясь на исторической вариации переменной")
        await callback.message.answer("Вам будет необходимо выбрать ту колонку, которую вы хотите выбрать в качестве ковариаты")
        await callback.message.answer("Данные будут изменены, вернуть их не будет представляться возможным")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = f"confirm_cuped_{dataset_id}",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )



@router.callback_query(F.data.startswith("confirm_cuped_"))
async def ask_history_file(callback: CallbackQuery, state: FSMContext):
    try:
        dataset_id = callback.data.split("_")[2]
        await state.update_data(id=dataset_id)
        await state.set_state(Cuped.waiting_for_history_file)

        await callback.message.answer("Пожалуйста, загрузите CSV-файл с историческими данными.\nОн должен содержать колонку, которую вы хотите использовать как ковариату.")
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Произошла ошибка, попробуйте позже.", reply_markup=inline_user_keyboards.home)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )



@router.message(Cuped.waiting_for_history_file, F.document)
async def receive_history_file(message: Message, state: FSMContext):
    try:
        document = message.document
        if not document.file_name.endswith(".csv"):
            await message.answer("Пожалуйста, загрузите CSV-файл.")
            return

        await state.update_data(history_file_id=document.file_id)

        file_info = await message.bot.get_file(document.file_id)
        file_bytes = await message.bot.download_file(file_info.file_path)

        df = pd.read_csv(BytesIO(file_bytes.read()))
        columns = df.columns.tolist()

        await message.answer(
            "Какую колонку вы хотите выбрать в качестве исторической ковариаты?",
            reply_markup=create_reply_column_keyboard_group(columns=columns)
        )
        await state.set_state(Cuped.select_history_column)
    except Exception as e:
        logging.exception(e)
        await message.answer("Ошибка при обработке файла. Попробуйте снова.")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )



@router.message(Cuped.select_history_column)
async def finish_cuped(message: Message, state: FSMContext):
    try:
        history_col = message.text
        data = await state.get_data()
        dataset_id = data.get("id")
        file_id = data.get("history_file_id")

        if not file_id:
            raise ValueError("Не удалось получить файл с историческими данными")


        file_info = await message.bot.get_file(file_id)
        file_bytes = await message.bot.download_file(file_info.file_path)


        history_df = pd.read_csv(BytesIO(file_bytes.getvalue()))
        if history_col not in history_df.columns:
            await message.answer("Колонка не найдена в файле. Пожалуйста, выберите одну из предложенных.")
            return

        response = await stats_handlers.cuped(
            telegram_id=message.from_user.id,
            id=dataset_id,
            history_column=history_col,
            history_df=history_df
        )

        if not response:
            raise ValueError("Ошибка при выполнении CUPED")

        await message.answer(
            "Данные успешно изменены!",
            reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=dataset_id)
        )
        await state.clear()

    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, произошла ошибка, попробуйте позже.", reply_markup=inline_user_keyboards.home)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


#===========================================================================================================================
# CUPAC
#===========================================================================================================================



@router.callback_query(F.data.startswith("cupac_"))
async def cupac_start(callback: CallbackQuery, state:FSMContext):
    try:
        await state.clear()
        dataset_id = callback.data.split("_")[1]
        await state.update_data(id = dataset_id)
        await state.set_state(Confirm.bundle)
        await callback.message.answer("CUPAC - Controlled-experiment Using Prediction As Covariate")
        await callback.message.answer("Мощный метод по повышения качества выборок")
        await callback.message.answer("В методе используется регрессионная модель. Вам будет необходимо указать на каких колонках мы будем учить модель. Убедитесь что эти колонки есть как в историческом датафрейме, так и в текущем датасете с тестом и контролем")
        await callback.message.answer("Откатить результаты будет невозможно")
        await callback.message.answer("Вы уверены, что хотите продолжить?", reply_markup= await inline_keyboards.get_confirm_menu(
            true_callback = f"confirm_cupac_{dataset_id}",
            false_callback = f"dataset_{dataset_id}"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, произошла ошибка, попробуйте позже")
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )




@router.callback_query(F.data.startswith("confirm_cupac_"))
async def ask_history_file_cupac(callback: CallbackQuery, state: FSMContext):
    try:
        dataset_id = callback.data.split("_")[2]
        await state.update_data(id=dataset_id)
        await state.set_state(Cupac.waiting_for_history_file)

        await callback.message.answer(
            "Пожалуйста, загрузите CSV-файл с историческими данными.\nОн должен содержать целевую метрику и фичи для обучения модели."
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Произошла ошибка, попробуйте позже.", reply_markup=inline_user_keyboards.home)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )



@router.message(Cupac.waiting_for_history_file, F.document)
async def receive_history_file_cupac(message: Message, state: FSMContext):
    try:
        document = message.document
        if not document.file_name.endswith(".csv"):
            await message.answer("Пожалуйста, загрузите CSV-файл.")
            return

        await state.update_data(history_file_id=document.file_id)

        file_info = await message.bot.get_file(document.file_id)
        file_bytes = await message.bot.download_file(file_info.file_path)

        df = pd.read_csv(BytesIO(file_bytes.read()))
        columns = df.columns.tolist()

        await state.update_data(columns=columns)

        await message.answer(
            "Выберите колонку, которую будем предсказывать (целевую метрику)",
            reply_markup=create_reply_column_keyboard_group(columns)
        )
        await state.set_state(Cupac.select_target_metric)
    except Exception as e:
        logging.exception(e)
        await message.answer("Ошибка при обработке файла.")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.message(Cupac.select_target_metric)
async def receive_target_metric(message: Message, state: FSMContext):
    try:
        metric = message.text
        data = await state.get_data()
        if metric not in data["columns"]:
            await message.answer("Колонка не найдена. Выберите из предложенных.")
            return

        await state.update_data(target_metric=metric)
        all_columns = data.get("columns", [])
        await state.update_data(feature_cols=[])
        await message.answer(
            "Теперь выберите одну или несколько колонок, которые будем использовать как признаки.\nКогда закончите, введите 'готово'",
            reply_markup=create_reply_column_keyboard_group(all_columns)
        )

        await state.set_state(Cupac.select_feature_columns)
    except Exception as e:
        logging.exception(e)
        await message.answer("Ошибка при выборе метрики.")
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )



@router.message(Cupac.select_feature_columns)
async def finish_cupac(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        feature_cols = data.get("feature_cols", [])
        
        if message.text.strip().lower() == "готово":
            if not feature_cols:
                await message.answer("Сначала выберите хотя бы одну колонку-признак!")
                return
            
            await message.answer("Уже обучаю модель...")
            all_columns = data.get("columns", [])
            invalid_columns = [col for col in feature_cols if col not in all_columns]
            
            if invalid_columns:
                await message.answer(f"Некорректные колонки: {', '.join(invalid_columns)}")
                return
            logging.info(f"Selected feature columns: {feature_cols}")
            logging.info(f"Total features count: {len(feature_cols)}")

            file_id = data["history_file_id"]
            file_info = await message.bot.get_file(file_id)
            file_bytes = await message.bot.download_file(file_info.file_path)
            df = pd.read_csv(BytesIO(file_bytes.getvalue()))

            response = await stats_handlers.cupac(
                telegram_id=message.from_user.id,
                id=data["id"],
                feature_columns=feature_cols,
                target_metric=data["target_metric"],
                history_df=df
            )

            if not response:
                raise ValueError("Ошибка при выполнении CUPAC")

            await message.answer(
                "Данные успешно изменены!",
                reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id=data["id"])
            )
            await state.clear()
            
        else:

            new_feature = message.text.strip()

            all_columns = data.get("columns", [])
            if new_feature not in all_columns:
                await message.answer("Колонка не найдена. Выберите из предложенных.")
                return

            if new_feature in feature_cols:
                await message.answer("Эта колонка уже выбрана!")
                return

            feature_cols.append(new_feature)
            await state.update_data(feature_cols=feature_cols)

            await message.answer(f"Колонка '{new_feature}' принята!")
            await message.answer(
                f"Выбрано колонок: {len(feature_cols)}\n"
                f"Текущий список: {', '.join(feature_cols)}\n\n"
                "Можете продолжить выбор колонок.\nКогда закончите, введите 'готово'",
                reply_markup=create_reply_column_keyboard_group(all_columns)
            )
            
    except Exception as e:
        logging.exception(f"Ошибка в finish_cupac: {e}")
        await message.answer("Произошла ошибка при выполнении CUPAC. попробуйте позже.", reply_markup=inline_user_keyboards.home)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )