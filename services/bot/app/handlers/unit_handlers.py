from app.handlers.router import unit_router as router
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

from app.states.states import Unit, UnitEdit, SendNew, File, Cohort
from app.requests.reports.delete_report import delete_report
from app.requests.reports.get_report import get_report, get_user_report
from app.requests.reports.post_report import post_report
from app.requests.reports.put_report import put_report


from app.keyboards import inline_user as keyboards


#========================================================================================================================================================================
#========================================================================================================================================================================
# UNIT ECONOMICS BLOCK
#========================================================================================================================================================================
#========================================================================================================================================================================

@router.callback_query(F.data == "unit_menu")
async def catalogue_callback_admin(callback: CallbackQuery):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload="catalogue"
    )
    post_models = await get_user_report(telegram_id=callback.from_user.id)
    await callback.message.answer("Вот доступные проекты 👇", reply_markup= await keyboards.get_reports(reports=post_models))
    await callback.answer()



@router.callback_query(F.data.startswith("report_"))
async def post_catalogue_callback_admin(callback: CallbackQuery):
    await callback.answer()
    post_id = callback.data.split("_")[1]
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="menu",
        payload=f"post_{post_id}"
    )
    post_data = await get_report(
        telegram_id=callback.from_user.id,
        report_id=post_id
    )
    if not post_data or isinstance(post_data, list):
        await callback.message.answer("Извините, не удалось получить доступ к позиции", reply_markup=inline_keyboards.home)
        return

    message_text = (
        f"📦 **Информация об юните:**\n\n"
        f"**Название:** `{post_data.get('name')}`\n"
        f"**Users:** `{post_data.get('users')}`\n"
        f"**Customers:** `{post_data.get('customers')}`\n"
        f"**avp:** `{post_data.get('avp')}`\n"
        f"**apc:** `{post_data.get('apc')}`\n"
        f"**tms:** `{post_data.get('tms')}`\n"
        f"**cogs:** `{post_data.get('cogs')}`\n"
        f"**cogs1s:** `{post_data.get('cogs1s')}`\n"
        f"**fc:** `{post_data.get('fc')}`\n"
    )

    await callback.message.answer(
        text=message_text,
        parse_mode="MarkdownV2",
        reply_markup=await inline_keyboards.get_report_menu(
            report_id=post_id,
        )
    )

#===========================================================================================================================
# Создание юнита
#===========================================================================================================================
@router.callback_query(F.data.startswith("create_report"))
async def post_create_callback_admin(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="create_unit"
    )
    await callback.answer()
    await state.clear()
    await callback.message.answer("Введите название проекта")
    await state.set_state(Unit.name)


@router.message(Unit.name)
async def post_enter_name_admin(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Введите валидное имя проекта")
        return
    await state.update_data(name=name)
    await state.set_state(Unit.users)
    await message.answer("Введите количество привлеченных пользователей")


@router.message(Unit.users)
async def post_enter_description_admin(message: Message, state: FSMContext):
    users = message.text.strip()
    if not users.isdigit():
        await message.answer("Введите валидное число привлеченных пользователей")
        return
    await state.update_data(users=int(users))
    await state.set_state(Unit.customers)
    await message.answer("Введите количество полученных клиентов")


@router.message(Unit.customers)
async def post_enter_price_admin(message: Message, state: FSMContext):
    customers = message.text.strip()
    if not customers.isdigit():
        await message.answer("Введите валидное число полученных клиентов")
        return
    await state.update_data(customers=int(customers))
    await state.set_state(Unit.avp)
    await message.answer("Введите avp (Average Value of Payment)")


@router.message(Unit.avp)
async def post_enter_country_admin(message: Message, state: FSMContext):
    avp = message.text.strip()
    if not avp.isdigit():
        await message.answer("Введите валидное число avp (Average Value of Payment)")
        return
    await state.update_data(avp=int(avp))
    await state.set_state(Unit.apc)
    await message.answer("Введите apc (Average Purchase Count)")


@router.message(Unit.apc)
async def post_enter_apc_admin(message: Message, state: FSMContext):
    apc = message.text.strip()
    if not apc.isdigit():
        await message.answer("Введите валидное число apc (Average Purchase Count)")
        return
    await state.update_data(apc=int(apc))
    await state.set_state(Unit.tms)
    await message.answer("Введите tms (Total Marketing Spends)")


@router.message(Unit.tms)
async def post_enter_tms_admin(message: Message, state: FSMContext):
    tms = message.text.strip()
    if not tms.isdigit():
        await message.answer("Введите валидное число tms (Total Marketing Spends)")
        return
    await state.update_data(tms=int(tms))
    await state.set_state(Unit.cogs)
    await message.answer("Введите cogs (Cost of goods sold)")


@router.message(Unit.cogs)
async def post_enter_cogs_admin(message: Message, state: FSMContext):
    cogs = message.text.strip()
    if not cogs.isdigit():
        await message.answer("Введите валидное число cogs (Cost of goods sold)")
        return
    await state.update_data(cogs=int(cogs))
    await state.set_state(Unit.cogs1s)
    await message.answer("Введите cogs1s (Cost of goods sold first sale)")


@router.message(Unit.cogs1s)
async def post_enter_cogs1s_admin(message: Message, state: FSMContext):
    cogs1s = message.text.strip()
    if not cogs1s.isdigit():
        await message.answer("Введите валидное число cogs1s (Cost of goods sold first sale)")
        return
    await state.update_data(cogs1s=int(cogs1s))
    await state.set_state(Unit.fc)
    await message.answer("Введите fc (Fixed Costs)")


@router.message(Unit.fc)
async def post_enter_fc_admin(message: Message, state: FSMContext):
    fc = message.text.strip()
    if not fc.isdigit():
        await message.answer("Введите валидное число fc (Fixed Costs)")
        return

    await state.update_data(fc=int(fc))
    data = await state.get_data()
    unit_data = await post_report(
        telegram_id=message.from_user.id,
        description="Модель юнит-экономики",
        name=data.get("name"),
        users=data.get("users"),
        customers=data.get("customers"),
        avp=data.get("avp"),
        apc=data.get("apc"),
        tms=data.get("tms"),
        cogs=data.get("cogs"),
        cogs1s=data.get("cogs1s"),
        fc=data.get("fc"),
    )
    if not unit_data:
        await message.answer("Ошибка при создании юнита", reply_markup=inline_keyboards.main)
        return

    msg = (
        f"🧩 **Модель успешно создана:**\n\n"
        f"**Название:** `{unit_data.get('name')}`\n"
        f"**Пользователи:** `{unit_data.get('users')}`\n"
        f"**Клиенты:** `{unit_data.get('customers')}`\n"
        f"**avp:** `{unit_data.get('avp')}`\n"
        f"**apc:** `{unit_data.get('apc')}`\n"
        f"**tms:** `{unit_data.get('tms')}`\n"
        f"**cogs:** `{unit_data.get('cogs')}`\n"
        f"**cogs1s:** `{unit_data.get('cogs1s')}`\n"
        f"**fc:** `{unit_data.get('fc')}`"
    )
    await message.answer(msg, parse_mode="MarkdownV2", reply_markup=await inline_keyboards.get_report_menu(report_id=unit_data.get("id")))
    await state.clear()

#===========================================================================================================================
# Редактирование поста
#===========================================================================================================================
@router.callback_query(F.data.startswith("edit_report_"))
async def post_edit_callback_admin(callback: CallbackQuery, state: FSMContext):
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="edit_post"
    )
    await callback.answer()
    await state.clear()
    category_id, unit_id = callback.data.split("_")[2:]
    await state.update_data(category_id=category_id)
    await state.update_data(post_id=unit_id)
    await callback.message.answer("Введите новое название модели")
    await state.set_state(UnitEdit.handle_edit_unit)


@router.message(UnitEdit.handle_edit_unit)
async def post_edit_name_admin(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Введите валидное имя модели")
        return
    await state.update_data(name=name)
    await state.set_state(UnitEdit.users)
    await message.answer("Введите значение users")


@router.message(UnitEdit.users)
async def post_edit_users_admin(message: Message, state: FSMContext):
    users = message.text.strip()
    if not users.isdigit():
        await message.answer("Введите валидное число пользователей")
        return
    await state.update_data(users=int(users))
    await state.set_state(UnitEdit.customers)
    await message.answer("Введите значение customers")


@router.message(UnitEdit.customers)
async def post_edit_customers_admin(message: Message, state: FSMContext):
    customers = message.text.strip()
    if not customers.isdigit():
        await message.answer("Введите валидное число клиентов")
        return
    await state.update_data(customers=int(customers))
    await state.set_state(UnitEdit.avp)
    await message.answer("Введите значение avp")


@router.message(UnitEdit.avp)
async def post_edit_avp_admin(message: Message, state: FSMContext):
    avp = message.text.strip()
    if not avp.isdigit():
        await message.answer("Введите валидное значение avp")
        return
    await state.update_data(avp=int(avp))
    await state.set_state(UnitEdit.apc)
    await message.answer("Введите значение apc")


@router.message(UnitEdit.apc)
async def post_edit_apc_admin(message: Message, state: FSMContext):
    apc = message.text.strip()
    if not apc.isdigit():
        await message.answer("Введите валидное значение apc")
        return
    await state.update_data(apc=int(apc))
    await state.set_state(UnitEdit.tms)
    await message.answer("Введите значение tms")


@router.message(UnitEdit.tms)
async def post_edit_tms_admin(message: Message, state: FSMContext):
    tms = message.text.strip()
    if not tms.isdigit():
        await message.answer("Введите валидное значение tms")
        return
    await state.update_data(tms=int(tms))
    await state.set_state(UnitEdit.cogs)
    await message.answer("Введите значение cogs")


@router.message(UnitEdit.cogs)
async def post_edit_cogs_admin(message: Message, state: FSMContext):
    cogs = message.text.strip()
    if not cogs.isdigit():
        await message.answer("Введите валидное значение cogs")
        return
    await state.update_data(cogs=int(cogs))
    await state.set_state(UnitEdit.cogs1s)
    await message.answer("Введите значение cogs1s")


@router.message(UnitEdit.cogs1s)
async def post_edit_cogs1s_admin(message: Message, state: FSMContext):
    cogs1s = message.text.strip()
    if not cogs1s.isdigit():
        await message.answer("Введите валидное значение cogs1s")
        return
    await state.update_data(cogs1s=int(cogs1s))
    await state.set_state(UnitEdit.fc)
    await message.answer("Введите значение fc")


@router.message(UnitEdit.fc)
async def post_edit_fc_admin(message: Message, state: FSMContext):
    fc = message.text.strip()
    if not fc.isdigit():
        await message.answer("Введите валидное значение fc")
        return

    data = await state.get_data()
    logging.warning(f"DATA: {data}")
    unit_data = await put_report(
        telegram_id=message.from_user.id,
        report_id=data.get("post_id"),
        description="Unit economics model",
        user_id=message.from_user.id,
        name=data.get("name"),
        users=data.get("users"),
        customers=data.get("customers"),
        avp=data.get("avp"),
        apc=data.get("apc"),
        tms=data.get("tms"),
        cogs=data.get("cogs"),
        cogs1s=data.get("cogs1s"),
        fc=int(fc),
    )

    if not unit_data:
        await message.answer("Ошибка при обновлении модели", reply_markup=await get_catalogue(telegram_id=message.from_user.id))
        return

    await message.answer("Модель успешно обновлена")
    message_text = (
        f"🔧 **Обновлённая модель:**\n\n"
        f"**Название:** `{unit_data.get('name')}`\n"
        f"**Users:** `{unit_data.get('users')}`\n"
        f"**Customers:** `{unit_data.get('customers')}`\n"
        f"**avp:** `{unit_data.get('avp')}`\n"
        f"**apc:** `{unit_data.get('apc')}`\n"
        f"**tms:** `{unit_data.get('tms')}`\n"
        f"**cogs:** `{unit_data.get('cogs')}`\n"
        f"**cogs1s:** `{unit_data.get('cogs1s')}`\n"
        f"**fc:** `{unit_data.get('fc')}`"
    )

    await message.answer(
        message_text,
        reply_markup=await inline_keyboards.get_post_menu(
            category_id=data.get("category_id"),
            post_id=data.get("post_id")
        ),
        parse_mode="MarkdownV2"
    )
    await state.clear()

#===========================================================================================================================
# Удаление поста
#===========================================================================================================================

@router.callback_query(F.data.startswith("delete_post_"))
async def post_delete_callback_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    post_id = callback.data.split("_")[2]
    response = await delete_report(telegram_id=callback.from_user.id, report_id=int(post_id))
    if not response:
        await callback.message.answer("Извините, не удалось удалить пост",reply_markup=inline_keyboards.main)
    await callback.message.answer("Пост успешно удален",reply_markup= inline_keyboards.main)
    await state.clear()
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="callback",
        source="inline",
        payload="delete_post"
    )

