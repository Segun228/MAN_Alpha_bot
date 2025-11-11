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

from app.requests.get.get_datasets import get_datasets, retrieve_dataset, get_dataset_file
from app.requests.get.get_distributions import get_distributions, retrieve_distribution

from app.requests.post.post_dataset import post_dataset
from app.requests.post.post_distribution import post_distribution

from app.requests.put.put_dataset import put_dataset
from app.requests.put.put_distribution import put_distribution

from app.requests.delete.delete_dataset import delete_dataset
from app.requests.delete.deleteDistribution import delete_distribution


#===========================================================================================================================
# Конфигурация основных маршрутов
#===========================================================================================================================


@router.message(CommandStart(), IsAdmin())
async def cmd_start_admin(message: Message, state: FSMContext):
    data = await login(telegram_id=message.from_user.id)
    if data is None:
        logging.error("Error while logging in")
        await message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await message.reply("Приветствую! 👋")
    await message.answer("Я предоставляю полный инструментарий для МатСтата и АБтестов")
    await message.answer("Сейчас ты можешь создавать, удалять и изменять распределения, а также добавлять свои датасеты в формате CSV")
    await message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await state.clear()
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="start"
    )


@router.callback_query(F.data == "restart")
async def callback_start_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    data = await login(telegram_id=callback.from_user.id)
    if data is None:
        logging.error("Error while logging in")
        await callback.message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await callback.message.reply("Приветствую! 👋")
    await callback.message.answer("Я предоставляю полный инструментарий для МатСтата и АБтестов")
    await callback.message.answer("Сейчас ты можешь создавать, удалять и изменять распределения, а также добавлять свои датасеты в формате CSV")
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
    await message.reply(text="Этот бот предоставляет доступ к инструментам статистического анализа, а также он специализирован для проведения АБ тестов\n\n Он может выполнять несколько интересных функций \n\nВы можете выбирать интересующие вас функции, в каждой из них вам будут предоставлены инструкции\n\nЕсли у вас остались вопросы, звоните нам или пишите в тех поддержку, мы всегда на связи:\n\n@dianabol_metandienon_enjoyer", reply_markup=inline_keyboards.home)

@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="contacts"
    )
    text = "Связь с разрабом: 📞\n\n\\@dianabol\\_metandienon\\_енjoyer 🤝"
    await message.reply(text=text, reply_markup=inline_keyboards.home, parse_mode='MarkdownV2')

@router.callback_query(F.data == "contacts")
async def contacts_callback(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="contacts"
    )
    text = "Связь с разрабом: 📞\n\n\\@dianabol\\_metandienon\\_enjoyer 🤝"
    await callback.message.edit_text(text=text, reply_markup=inline_keyboards.home, parse_mode='MarkdownV2')
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="main_menu"
    )
    await callback.message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await callback.answer()

#===========================================================================================================================
# Каталог
#===========================================================================================================================
@router.callback_query(F.data == "catalogue")
async def catalogue_callback_admin(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="catalogue"
    )
    await callback.message.answer("Что именно вас интересует?👇", reply_markup = inline_keyboards.catalogue_choice)
    await callback.answer()


@router.callback_query(F.data == "distributions")
async def get_distributions_inline_catalogue(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Отлично, вот ваши распределения!", reply_markup = await inline_keyboards.get_distributions_catalogue(telegram_id=callback.from_user.id))




@router.callback_query(F.data == "datasets")
async def get_datasets_inline_catalogue(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Отлично, вот ваши датасеты!", reply_markup = await inline_keyboards.get_datasets_catalogue(telegram_id=callback.from_user.id))


@router.callback_query(F.data.startswith("distribution_"))
async def distribution_catalogue_callback_admin(callback: CallbackQuery):
    try:
        await callback.answer()
        distribution_id = callback.data.split("_")[1]
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="callback",
            source="menu",
            payload=f"distribution_{distribution_id}"
        )
        current_distribution = await retrieve_distribution(telegram_id=callback.from_user.id, distribution_id=distribution_id)
        if current_distribution is None:
            await callback.message.answer("Извините, тут пока пусто, возвращаейтесь позже!", reply_markup= await get_distributions_catalogue(telegram_id=callback.from_user.id))
            await callback.answer()
            return
        data = current_distribution

        params = json.loads(data['distribution_parameters'].replace("'", '"'))
        param_string = "\n"
        for key, value in params.items():
            param_string += f" \- *{key.replace(".", "\.")}* \= {value.replace(".", "\.")}\n"
        param_string += "\n\n"
        msg = (
            f"*Name:* {data['name']}\n"
            f"*Type:* {data['distribution_type']}\n"
            f"*Parameters:* {param_string}"
        )
        await callback.message.answer(msg, parse_mode="MarkdownV2", reply_markup=await inline_keyboards.get_distribution_single_menu(distribution_id = distribution_id, telegram_id = callback.from_user.id, distribution = current_distribution))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, не удалось загрузить распределение", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=callback.from_user.id))
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


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

@router.callback_query(F.data.startswith("dataset_"))
async def dataset_catalogue_callback_admin(callback: CallbackQuery, bot:Bot):
    try:
        await callback.answer()
        dataset_id = callback.data.split("_")[1]
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="callback",
            source="menu",
            payload=f"dataset_{dataset_id}"
        )
        current_dataset = await retrieve_dataset(telegram_id=callback.from_user.id, dataset_id=dataset_id)
        if current_dataset is None:
            await callback.message.answer("Извините, тут пока пусто, возвращаейтесь позже!", reply_markup= await get_distributions_catalogue(telegram_id=callback.from_user.id))
            await callback.answer()
            return
        data = current_dataset


        name = escape_md(data['name'])
        alpha = escape_md(str(data['alpha']))
        beta = escape_md(str(data['beta']))
        test = escape_md(str(data['test']) or "Not set yet")
        control = escape_md(str(data['control']) or "Not set yet")
        length = escape_md(str(data['length']) or "Not set yet")


        params = data['columns']
        param_string = "\n"
        for nam in params:
            escaped_nam = escape_md(nam)
            param_string += f"{escaped_nam}\n"
        param_string += "\n"
        
        msg = (
            f"*Name:* {name}\n\n"
            f"*Columns:* {param_string}"
            f"*Alpha:* {alpha}\n"
            f"*Beta:* {beta}\n\n"
            f"*Test group:* {test}\n"
            f"*Controle group:* {control}\n\n"
            f"*Final length:* {length}\n"
        )
        await callback.message.answer(msg, parse_mode="MarkdownV2", reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id = dataset_id))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, не удалось загрузить датасет", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=callback.from_user.id))
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="error handled",
            platform="bot",
            is_authenticated=True,
            source="error handler",
            level="ERROR",
            payload=str(e)
        )


@router.callback_query(F.data.startswith("datasetfile_"))
async def dataset_get_file(callback: CallbackQuery, bot:Bot):
    try:
        await callback.answer()
        dataset_id = callback.data.split("_")[1]
        await build_log_message(
            telegram_id=callback.from_user.id,
            action="callback",
            source="menu",
            payload=f"dataset_{dataset_id}"
        )
        current_dataset = await retrieve_dataset(telegram_id=callback.from_user.id, dataset_id=dataset_id)
        if current_dataset is None:
            await callback.message.answer("Извините, тут пока пусто, возвращаейтесь позже!", reply_markup= await get_distributions_catalogue(telegram_id=callback.from_user.id))
            await callback.answer()
            return
        dataset_bytes = await get_dataset_file(
            telegram_id=callback.from_user.id,
            url=current_dataset.get("url")
        )
        if dataset_bytes:
            file = BufferedInputFile(
                file=dataset_bytes,
                filename="dataset.csv"
            )
            await bot.send_document(
                chat_id=callback.from_user.id,
                document=file
            )
        else:
            await callback.message.answer("Извините, не удалось загрузить датасет")
        data = current_dataset


        name = escape_md(data['name'])
        alpha = escape_md(str(data['alpha']))
        beta = escape_md(str(data['beta']))
        test = escape_md(str(data['test']) or "Not set yet")
        control = escape_md(str(data['control']) or "Not set yet")
        length = escape_md(str(data['length']) or "Not set yet")


        params = data['columns']
        param_string = "\n"
        for nam in params:
            escaped_nam = escape_md(nam)
            param_string += f"{escaped_nam}\n"
        param_string += "\n"
        
        msg = (
            f"*Name:* {name}\n\n"
            f"*Columns:* {param_string}"
            f"*Alpha:* {alpha}\n"
            f"*Beta:* {beta}\n\n"
            f"*Test group:* {test}\n"
            f"*Controle group:* {control}\n\n"
            f"*Final length:* {length}\n"
        )
        await callback.message.answer(msg, parse_mode="MarkdownV2", reply_markup=await inline_keyboards.get_dataset_single_menu(dataset_id = dataset_id))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, не удалось загрузить датасет", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=callback.from_user.id))
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
# Создание распределения
#===========================================================================================================================

@router.callback_query(F.data == "create_distribution")
async def distribution_create_callback(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="create_distribution"
    )
    await state.clear()
    await callback.message.answer("Введите название нового распределения")
    await state.set_state(Distribution.name)
    await callback.answer()


@router.message( Distribution.name)
async def choose_distrib_type(message: Message, state: FSMContext):
    await state.set_state(Distribution.distribution_type)
    name = (message.text).strip()
    await state.update_data(name = name)
    current_state = await state.get_state()
    await message.answer("Выберите необходимый тип распределения", reply_markup=await inline_keyboards.choose_distribution_type())



@router.callback_query(F.data, Distribution.distribution_type)
async def distribution_create_callback_admin_description(callback: CallbackQuery, state: FSMContext):
    distribution_type = (callback.data).strip()
    await state.update_data(distribution_type = distribution_type)
    msg = """
        *🎲 Выберите параметры для распределения*

        Введите параметры *через пробел*\. Ниже указаны параметры, которые поддерживаются для каждого распределения:

        _Примеры:_
        `mu sigma` — для `normal`  
        `a b loc scale` — для `beta`

        *Поддерживаемые распределения:*

        • `normal` — `mu sigma`  
        mu — математическое ожидание  
        sigma — стандартное отклонение

        • `uniform` — `loc scale`  
        loc — нижняя граница  
        scale — ширина \(scale \= верхняя \- нижняя\)

        • `exponential` — `loc scale`  
        loc — смещение  
        scale — параметр масштаба \(1/λ\)

        • `gamma` — `a loc scale`  
        a — shape \(форма\)  
        loc — смещение  
        scale — масштаб

        • `beta` — `a b loc scale`  
        a — alpha \(форма\)  
        b — beta \(форма\)  
        loc — смещение  
        scale — масштаб

        • `binomial` — `n p`  
        n — число испытаний  
        p — вероятность успеха

        • `poisson` — `mu`  
        mu — среднее число событий

        • `chi2` — `df loc scale`  
        df — степени свободы  
        loc — смещение  
        scale — масштаб

        • `t` — `df loc scale`  
        df — степени свободы  
        loc — смещение  
        scale — масштаб

        • `f` — `dfn dfd loc scale`  
        dfn — числитель степени свободы  
        dfd — знаменатель степени свободы  
        loc — смещение  
        scale — масштаб

        • `lognormal` — `s loc scale`  
        s — стандартное отклонение log  
        loc — смещение  
        scale — масштаб \(exp\(mean\)\)

        • `geometric` — `p`  
        p — вероятность успеха

        • `hypergeom` — `M n N`  
        M — общее количество объектов  
        n — количество "успешных" объектов  
        N — размер выборки

        • `negative_binomial` — `n p`  
        n — число успехов  
        p — вероятность успеха
        _Если вы введёте неправильное количество параметров, будет использовано значение по умолчанию:_  
        `normal` с параметрами `mu=0`, `sigma=1`
        """
    await callback.message.answer(text = msg, parse_mode="MarkdownV2")
    await state.set_state(Distribution.params)


@router.message(Distribution.params)
async def category_enter_name_admin(message: Message, state: FSMContext):
    params = list((message.text).strip().split(" "))
    data = await state.get_data()
    name = data.get("name")
    distribution_type = data.get("distribution_type").strip()
    distribution_params = {
        "normal": ["mu", "sigma"],
        "binomial": ["n", "p"],
        "poisson": ["mu"],
        "uniform": ["loc", "scale"],
        "exponential": ["loc", "scale"],
        "beta": ["a", "b", "loc", "scale"],
        "gamma": ["a", "loc", "scale"],
        "lognormal": ["s", "loc", "scale"],
        "chi2": ["df", "loc", "scale"],
        "t": ["df", "loc", "scale"],
        "f": ["dfn", "dfd", "loc", "scale"],
        "geometric": ["p"],
        "hypergeom": ["M", "n", "N"],
        "negative_binomial": ["n", "p"]
    }
    param_names = distribution_params[distribution_type]
    if len(param_names) != len(params):
        distribution_type = "normal"
        final_params = {
            "mu":0,
            "sigma":1
        }
    else:
        final_params = {}
        for nam, par in zip(param_names, params):
            final_params[nam] = par
    response = await post_distribution(telegram_id=message.from_user.id, name=name, distribution_type=distribution_type, distribution_parameters=final_params)
    if not response:
        await message.answer("Извините, не удалось создать распределение", reply_markup=inline_keyboards.main)
        return
    await message.answer("Распределение создано!", reply_markup= await get_distributions_catalogue(telegram_id = message.from_user.id))
    await state.clear()


#===========================================================================================================================
# Редактирование распределения
#===========================================================================================================================

@router.callback_query(F.data.startswith("edit_distribution"))
async def distribution_edit_callback(callback: CallbackQuery, state: FSMContext):
    distribution_id = callback.data.split("_")[2]
    await state.update_data(id = distribution_id)
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="edit_distribution"
    )
    await state.clear()
    await callback.message.answer("Введите название нового распределения")
    await state.set_state(Distribution.name)
    await callback.answer()


@router.message( Distribution.name)
async def choose_distrib_type_edit(message: Message, state: FSMContext):
    await state.set_state(Distribution.distribution_type)
    name = (message.text).strip()
    await state.update_data(name = name)
    current_state = await state.get_state()
    await message.answer("Выберите необходимый тип распределения", reply_markup=await inline_keyboards.choose_distribution_type())



@router.callback_query(F.data, Distribution.distribution_type)
async def distribution_edit_callback_admin_description(callback: CallbackQuery, state: FSMContext):
    distribution_type = (callback.data).strip()
    await state.update_data(distribution_type = distribution_type)
    msg = """
        *🎲 Выберите параметры для распределения*

        Введите параметры *через пробел*\. Ниже указаны параметры, которые поддерживаются для каждого распределения:

        _Примеры:_
        `mu sigma` — для `normal`  
        `a b loc scale` — для `beta`

        *Поддерживаемые распределения:*

        • `normal` — `mu sigma`  
        mu — математическое ожидание  
        sigma — стандартное отклонение

        • `uniform` — `loc scale`  
        loc — нижняя граница  
        scale — ширина \(scale \= верхняя \- нижняя\)

        • `exponential` — `loc scale`  
        loc — смещение  
        scale — параметр масштаба \(1/λ\)

        • `gamma` — `a loc scale`  
        a — shape \(форма\)  
        loc — смещение  
        scale — масштаб

        • `beta` — `a b loc scale`  
        a — alpha \(форма\)  
        b — beta \(форма\)  
        loc — смещение  
        scale — масштаб

        • `binomial` — `n p`  
        n — число испытаний  
        p — вероятность успеха

        • `poisson` — `mu`  
        mu — среднее число событий

        • `chi2` — `df loc scale`  
        df — степени свободы  
        loc — смещение  
        scale — масштаб

        • `t` — `df loc scale`  
        df — степени свободы  
        loc — смещение  
        scale — масштаб

        • `f` — `dfn dfd loc scale`  
        dfn — числитель степени свободы  
        dfd — знаменатель степени свободы  
        loc — смещение  
        scale — масштаб

        • `lognormal` — `s loc scale`  
        s — стандартное отклонение log  
        loc — смещение  
        scale — масштаб \(exp\(mean\)\)

        • `geometric` — `p`  
        p — вероятность успеха

        • `hypergeom` — `M n N`  
        M — общее количество объектов  
        n — количество "успешных" объектов  
        N — размер выборки

        • `negative_binomial` — `n p`  
        n — число успехов  
        p — вероятность успеха
        _Если вы введёте неправильное количество параметров, будет использовано значение по умолчанию:_  
        `normal` с параметрами `mu=0`, `sigma=1`
        """
    await callback.message.answer(text = msg, parse_mode="MarkdownV2")
    await state.set_state(Distribution.params)


@router.message(Distribution.params)
async def category_edit_name_admin(message: Message, state: FSMContext):
    params = list((message.text).strip().split(" "))
    data = await state.get_data()
    id = data.get("id")
    name = data.get("name")
    distribution_type = data.get("distribution_type").strip()
    distribution_params = {
        "normal": ["mu", "sigma"],
        "binomial": ["n", "p"],
        "poisson": ["mu"],
        "uniform": ["loc", "scale"],
        "exponential": ["loc", "scale"],
        "beta": ["a", "b", "loc", "scale"],
        "gamma": ["a", "loc", "scale"],
        "lognormal": ["s", "loc", "scale"],
        "chi2": ["df", "loc", "scale"],
        "t": ["df", "loc", "scale"],
        "f": ["dfn", "dfd", "loc", "scale"],
        "geometric": ["p"],
        "hypergeom": ["M", "n", "N"],
        "negative_binomial": ["n", "p"]
    }
    param_names = distribution_params[distribution_type]
    if len(param_names) != len(params):
        distribution_type = "normal"
        final_params = {
            "mu":0,
            "sigma":1
        }
    else:
        final_params = {}
        for nam, par in zip(param_names, params):
            final_params[nam] = par
    response = await put_distribution(telegram_id=message.from_user.id, distribution_id=id, name=name, distribution_type=distribution_type, distribution_parameters=final_params)
    if not response:
        await message.answer("Извините, не удалось изменить распределение", reply_markup=inline_keyboards.main)
        return
    await message.answer("Распределение изменено!", reply_markup= await get_distributions_catalogue(telegram_id = message.from_user.id))
    await state.clear()

#===========================================================================================================================
# Удаление распрделения 
#===========================================================================================================================

@router.callback_query(F.data.startswith("delete_distribution_"))
async def distribution_delete_callback_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    category_id = callback.data.split("_")[2]
    response = await delete_distribution(telegram_id=callback.from_user.id, distribution_id=category_id)
    if not response:
        await callback.message.answer("Извините, не удалось удалить распределение", reply_markup=inline_keyboards.main)
        return
    await callback.message.answer("Распределение удалено!", reply_markup=await get_distributions_catalogue(telegram_id = callback.from_user.id))
    await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="delete_distribution"
    )

#===========================================================================================================================
# Создание датасета
#===========================================================================================================================

@router.callback_query(F.data == "create_dataset")
async def dataset_create_callback(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="create_dataset"
    )
    await state.clear()
    await callback.message.answer("Введите название нового датасета")
    await state.set_state(Dataset.name)
    await callback.answer()


@router.message(Dataset.name)
async def load_dataset(message: Message, state: FSMContext):
    await state.set_state(Dataset.file)
    name = (message.text).strip()
    await state.update_data(name = name)
    await message.answer("Отправте файл CSV с датасетом")



@router.message(F.document, Dataset.file)
async def get_dataset_file_message(message: Message, state: FSMContext, bot:Bot):
    try:
        data = await state.get_data()
        file_id = message.document.file_id
        file_name = message.document.file_name
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_bytes = await bot.download_file(file_path)
        buffer = io.BytesIO()
        buffer.write(file_bytes.read())
        buffer.seek(0)  
        result = await post_dataset(telegram_id=message.from_user.id, name=data.get("name", file_name), csv_buffer=buffer)
        if not result:
            await message.answer("Ошибка при загрузке файла", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=message.from_user.id))
        else:
            await message.answer("Датасет успешно загружен!", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=message.from_user.id))
        await state.clear()
    except Exception as e:
        logging.exception(e)
        logging.error("Error while loading the dataset")
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
# Редактирование датасета
#===========================================================================================================================

@router.callback_query(F.data.startswith("edit_dataset"))
async def dataset_edit_callback(callback: CallbackQuery, state: FSMContext):
    dataset_id = callback.data.strip().split("_")[2]
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="edit_dataset"
    )
    await state.clear()
    await state.update_data(id = dataset_id)
    await callback.message.answer("Введите название нового датасета")
    await state.set_state(DatasetEdit.name)
    await callback.answer()


@router.message(DatasetEdit.name)
async def edit_load_dataset(message: Message, state: FSMContext):
    await state.set_state(DatasetEdit.file)
    name = (message.text).strip()
    await state.update_data(name = name)
    await message.answer("Отправте файл CSV с датасетом")



@router.message(F.document, DatasetEdit.file)
async def get_dataset_file_msg(message: Message, state: FSMContext, bot:Bot):
    try:
        data = await state.get_data()
        dataset_id = data.get("id")
        if not dataset_id:
            raise ValueError("Error while loading dataset id")
        file_id = message.document.file_id
        file_name = message.document.file_name
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_bytes = await bot.download_file(file_path)
        buffer = io.BytesIO()
        buffer.write(file_bytes.read())
        buffer.seek(0)  
        result = await put_dataset(telegram_id=message.from_user.id, dataset_id=dataset_id, name=data.get("name", file_name), csv_buffer=buffer)
        if not result:
            await message.answer("Ошибка при загрузке файла", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=message.from_user.id))
        else:
            await message.answer("Датасет успешно загружен!", reply_markup=await inline_keyboards.get_datasets_catalogue(telegram_id=message.from_user.id))
        await state.clear()
    except Exception as e:
        logging.exception(e)
        logging.error("Error while loading the dataset")
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
# Удаление датасета
#===========================================================================================================================

@router.callback_query(F.data.startswith("delete_dataset_"))
async def dataset_delete_callback_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    category_id = callback.data.split("_")[2]
    response = await delete_dataset(telegram_id=callback.from_user.id, dataset_id=category_id)
    if not response:
        await callback.message.answer("Извините, не удалось удалить dataset", reply_markup=inline_keyboards.main)
        return
    await callback.message.answer("Датасет удален!", reply_markup=await get_distributions_catalogue(telegram_id = callback.from_user.id))
    await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="delete_dataset"
    )
