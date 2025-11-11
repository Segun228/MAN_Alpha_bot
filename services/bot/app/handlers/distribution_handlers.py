from app.handlers.router import distribution_router as router
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

from app.states.states import Send, File, Distribution, Dataset, DistributionEdit, DatasetEdit

from aiogram.types import BufferedInputFile


from app.keyboards.inline_user import get_datasets_catalogue, get_distributions_catalogue

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

from app.requests.distribution.get_plot import get_plot
import app.requests.distribution.get_plot as getter
from app.states.states import Probability, Interval, Sample, Quantile, Percentile


#============================================================================================================================================================
# График
#============================================================================================================================================================


@router.callback_query(F.data.startswith("get_plot_"))
async def get_plot_start(callback: CallbackQuery, state: FSMContext, bot:Bot):
    await callback.message.answer("Рисую график...")
    try:
        id = int(callback.data.split("_")[2])
        await state.clear()
        zip_buf = await get_plot(
            telegram_id= callback.from_user.id,
            id = id,
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.img', '.jpg', '.jpeg')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=callback.from_user.id, document=document)
        await callback.message.answer("Ваше распределение готово!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )


#============================================================================================================================================================
# Вероятность
#============================================================================================================================================================
@router.callback_query(F.data.startswith("get_probability_"))
async def get_probability_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    distribution_id = callback.data.split("_")[2]
    await callback.message.answer("Введите необходимое значение")
    await state.set_state(Probability.probability)
    await state.update_data(id = distribution_id)
    return

@router.message(Probability.probability)
async def get_probability_end(message:Message, state: FSMContext, bot:Bot):
    data = await state.get_data()
    id = data.get("id")
    await message.answer("Рисую график...")
    try:
        a = float(message.text)
        zip_buf = await getter.get_probability(
            telegram_id= message.from_user.id,
            id = id,
            a = a
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.img', '.jpg', '.jpeg')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваше распределение готово!", reply_markup= inline_keyboards.main)
    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )


#============================================================================================================================================================
# Интервал
#============================================================================================================================================================



@router.callback_query(F.data.startswith("get_interval_"))
async def get_interval_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите значения интервала через пробел")
    await state.clear()
    distribution_id = callback.data.split("_")[2]
    await state.set_state(Interval.interval)
    await state.update_data(id = distribution_id)
    return


@router.message(Interval.interval)
async def get_interval_end(message:Message, state: FSMContext, bot:Bot):
    data = await state.get_data()
    id = data.get("id")
    await message.answer("Рисую график...")
    try:
        a, b = list(map(float, message.text.strip().split()))
        zip_buf = await getter.get_interval(
            telegram_id= message.from_user.id,
            id = id,
            a=a,
            b=b
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.img', '.jpg', '.jpeg')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваше распределение готово!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )

#============================================================================================================================================================
# Квантиль
#============================================================================================================================================================

@router.callback_query(F.data.startswith("get_quantile_"))
async def get_quantile_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    distribution_id = callback.data.split("_")[2]
    await callback.message.answer("Введите необходимое значение квантиля")
    await state.set_state(Quantile.quantile)
    await state.update_data(id = distribution_id)
    return



@router.message(Quantile.quantile)
async def get_quantile_end(message:Message, state: FSMContext, bot:Bot):
    data = await state.get_data()
    id = data.get("id")
    await message.answer("Рисую график...")
    try:
        a = float(message.text.strip())
        zip_buf = await getter.get_quantile(
            telegram_id= message.from_user.id,
            id = id,
            a=a
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.img', '.jpg', '.jpeg')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваше распределение готово!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )

#============================================================================================================================================================
# Персентиль
#============================================================================================================================================================

@router.callback_query(F.data.startswith("get_percentile_"))
async def get_percentile_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    distribution_id = callback.data.split("_")[2]
    await callback.message.answer("Введите необходимое значение персентиля")
    await state.set_state(Percentile.percentile)
    await state.update_data(id = distribution_id)
    return



@router.message(Percentile.percentile)
async def get_percentile_end(message:Message, state: FSMContext, bot:Bot):
    data = await state.get_data()
    id = data.get("id")
    await message.answer("Рисую график...")
    try:
        a = float(message.text.strip())
        zip_buf = await getter.get_percentile(
            telegram_id= message.from_user.id,
            id = id,
            a=a
        )
        if not zip_buf:
            raise Exception("Error while getting report from the server")
        zip_buf = io.BytesIO(zip_buf)
        with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.png', '.img', '.jpg', '.jpeg')): 
                    file_bytes = zip_ref.read(filename)
                    file_buf = io.BytesIO(file_bytes)
                    file_buf.seek(0)

                    document = BufferedInputFile(file_buf.read(), filename=filename)
                    await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваше распределение готово!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )


#============================================================================================================================================================
# Выборка
#============================================================================================================================================================

@router.callback_query(F.data.startswith("get_sample_"))
async def get_sample_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    distribution_id = callback.data.split("_")[2]
    await callback.message.answer("Введите необходимое значение выборки")
    await state.set_state(Sample.sample)
    await state.update_data(id = distribution_id)
    return



@router.message(Sample.sample)
async def get_sample_end(message:Message, state: FSMContext, bot:Bot):
    data = await state.get_data()
    id = data.get("id")
    await message.answer("Выбираю вам значения...")
    try:
        n = int(message.text.strip())
        xlsx_buf = await getter.get_sample(
            telegram_id= message.from_user.id,
            id = id,
            n=n
        )
        if not xlsx_buf:
            raise Exception("Error while getting report from the server")
        xlsx_buf = io.BytesIO(xlsx_buf)

        document = BufferedInputFile(xlsx_buf.read(), filename="distribution.xlsx")
        await bot.send_document(chat_id=message.from_user.id, document=document)
        await message.answer("Ваше распределение готово!", reply_markup= inline_keyboards.main)

    except Exception as e:
        logging.exception(e)
        await message.answer("Возникла ошибка при анализе", reply_markup= inline_keyboards.main)
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )
        raise
    finally:
        await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="callback",
        source="inline",
        payload="visualize_set"
    )
