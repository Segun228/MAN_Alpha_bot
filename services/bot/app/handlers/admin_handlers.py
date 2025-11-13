from app.handlers.router import admin_router as router
import logging
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

from app.keyboards import inline_admin as inline_keyboards
from app.keyboards import inline_user as inline_user_keyboards

from app.states.states import Send

from aiogram.types import BufferedInputFile


from app.keyboards.inline_user import get_distributions_catalogue, get_datasets_catalogue

from app.filters.IsAdmin import IsAdmin

from app.requests.user.login import login
from app.requests.helpers.get_cat_error import get_cat_error_async
from app.requests.get.get_datasets import get_datasets
from app.requests.get.get_distributions import get_distributions

from app.requests.helpers.get_cat_error import get_cat_error_async


from app.requests.user.get_alive import get_alive
from app.requests.user.make_admin import make_admin


from app.kafka.utils import build_log_message
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
    await message.reply("Приветствую Админ! 👋")
    await message.answer("Я ваш личный бизнес асистент")
    await message.answer("Я могу помочь вам с любыми бизнес вопросами, предложить новые идеи и предложить инсайты")
    await message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="start"
    )
    await state.clear()


@router.callback_query(F.data == "restart", IsAdmin())
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
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="inline",
        source="callback",
        payload="restart"
    )
    await callback.answer()


@router.message(Command("help"), IsAdmin())
async def cmd_help(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="help"
    )
    await message.reply(text="Этот бот предоставляет доступ к инструментам статистического анализа, а также он специализирован для проведения АБ тестов\n\n Он может выполнять несколько интересных функций \n\nВы можете выбирать интересующие вас функции, в каждой из них вам будут предоставлены инструкции\n\nЕсли у вас остались вопросы, звоните нам или пишите в тех поддержку, мы всегда на связи:\n\n@dianabol_metandienon_enjoyer", reply_markup=inline_keyboards.home)

@router.message(Command("contacts"), IsAdmin())
async def cmd_contacts(message: Message):
    await build_log_message(
        telegram_id=message.from_user.id,
        action="command",
        source="command",
        payload="contacts"
    )
    text = "Связь с разрабом: 📞\n\n\\@dianabol\\_metandienon\\_енjoyer 🤝"
    await message.reply(text=text, reply_markup=inline_keyboards.home, parse_mode='MarkdownV2')

@router.callback_query(F.data == "contacts", IsAdmin())
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



#===========================================================================================================================
# Создание рассылки
#===========================================================================================================================


@router.callback_query(F.data == "send_menu", IsAdmin())
async def send_menu_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Напишите текст сообщения или прикрепите фото с подписью. ",
        reply_markup=inline_keyboards.catalogue
    )
    await state.set_state(Send.handle)
    return


@router.callback_query(F.data == "send_menu")
async def send_menu_admin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Send.handle)
    await callback.message.answer(
        "Извините, вы не обладаете достаточными правами",
        reply_markup=inline_keyboards.catalogue
    )
    return


@router.message(Send.handle, F.photo, IsAdmin())
async def send_photo_message(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    caption = message.caption or ""
    await state.update_data(photo=photo, caption=caption)
    await message.answer("Фото получено. Начинаю рассылку...")
    await start_broadcast(state, message, message.bot)


@router.message(Send.handle, F.text, IsAdmin())
async def send_text_message(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Текст получен. Начинаю рассылку...")
    await start_broadcast(state, message, message.bot)


async def start_broadcast(state: FSMContext, message: Message, bot: Bot):
    data = await state.get_data()
    users_data = await get_alive(telegram_id=message.from_user.id)

    if not users_data:
        await message.answer("Ошибка при рассылке. попробуйте позже.", reply_markup=inline_user_keyboards.home)
        await state.clear()
        return

    tasks = []
    for user in users_data:
        user_id = user.get("telegram_id")
        if "photo" in data:
            tasks.append(
                bot.send_photo(chat_id=user_id, photo=data["photo"], caption=data.get("caption", ""))
            )
        elif "text" in data:
            tasks.append(
                bot.send_message(chat_id=user_id, text=data["text"])
            )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_sends = sum(1 for r in results if not isinstance(r, TelegramAPIError))
    failed_sends = len(results) - successful_sends

    await message.answer(
        f"Рассылка завершена.\n✅ Успешно: {successful_sends}\n❌ Ошибки: {failed_sends}",
        reply_markup=inline_keyboards.main
    )
    await state.clear()

#===========================================================================================================================
# Разрешение доступа
#===========================================================================================================================


@router.callback_query(F.data.startswith("access_give"), IsAdmin())
async def give_acess_admin(callback: CallbackQuery, state: FSMContext, bot:Bot):
    request = str(callback.data)
    try:
        user_id = list(request.split("_"))[2]
        if not user_id:
            logging.error("Ошибка предоставления доступа")
            return
        response = await make_admin(
            telegram_id= callback.from_user.id,
            target_user_id= user_id
        )
        if not response:
            logging.error("Ошибка предоставления доступа")
            await bot.send_message(chat_id=int(user_id), text="К сожалению, вам было отказано в предоставлении прав администратора", reply_markup=inline_keyboards.home)
        else:
            logging.info(response)
            await callback.message.answer("Права администратора были успешно предоставлены", reply_markup=inline_keyboards.home)
            await bot.send_message(chat_id=user_id, text="Вам были предоставлены права администратора", reply_markup=inline_keyboards.home)
    except Exception as e:
        logging.error(e)


@router.callback_query(F.data.startswith("access_reject"), IsAdmin())
async def reject_acess_admin(callback: CallbackQuery, state: FSMContext, bot:Bot):
    request = str(callback.data)
    try:
        user_id = list(request.split("_"))[2]
        await bot.send_message(chat_id=int(user_id), text="К сожалению, вам было отказано в предоставлении прав администратора", reply_markup=inline_keyboards.home)
    except Exception as e:
        logging.error(e)
