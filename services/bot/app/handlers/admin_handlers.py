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

from app.filters.IsAdmin import IsAdmin

from app.requests.user.login import login
from app.requests.helpers.get_cat_error import get_cat_error_async

from app.requests.helpers.get_cat_error import get_cat_error_async


from app.requests.user.get_alive import get_alive
from app.requests.user.make_admin import make_admin


from app.kafka.utils import build_log_message
from app.states.states import CreateUser

from app.requests.post.post_user import post_user
from app.requests.post.post_poll_result import post_poll_result
from app.states import states
from app.requests.helpers.get_cat_photo import get_cat_photo
#===========================================================================================================================
# Конфигурация основных маршрутов
#===========================================================================================================================


@router.message(CommandStart(), IsAdmin())
async def cmd_start_admin(message: Message, state: FSMContext):
    data = await login(telegram_id=message.from_user.id)
    if data is None:
        logging.error("Error while logging admin in")
        await message.answer("Бот еще не проснулся, попробуйте немного подождать 😔", reply_markup=inline_keyboards.restart)
        return
    if data.get("status") in (404, 500):
        await state.set_state(CreateUser.start_creating)
        await message.answer("Админ, вы еще не зарегестрированы! Вам будет необходимо пройти короткую регистрацию")
        await message.answer("Введите ваше имя")
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
    if data.get("status") == 404:
        await state.set_state(CreateUser.start_creating)
        await callback.message.answer("Админ, вы еще не зарегестрированы! Вам будет необходимо пройти короткую регистрацию")
        await callback.message.answer("Введите ваше имя")
        return
    await state.update_data(telegram_id = data.get("telegram_id"))
    await callback.message.reply("Приветствую, Админ! 👋")
    await callback.message.answer("Я ваш личный бизнес асистент")
    await callback.message.answer("Я могу помочь вам с любыми бизнес вопросами, предложить новые идеи и предложить инсайты")
    await build_log_message(
        telegram_id=callback.from_user.id,
        action="inline",
        source="callback",
        payload="restart"
    )
    await callback.answer()

#===========================================================================================================================
# Регистрация юзера
#===========================================================================================================================


@router.message(CreateUser.start_creating, IsAdmin())
async def start_admin_user_create(message: Message, state: FSMContext):
    try:
        login = message.text
        if login:
            login = login.strip()
        await state.update_data(login = login)
        await message.answer("Имя получено!")
        await message.answer("Введите ваше почту")
        await state.set_state(CreateUser.login)
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка во время создания пользователя, попробуйте снова", reply_markup=inline_keyboards.restart)
        await state.clear()
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error",
            source="message",
            payload="error"
        )
        return


@router.message(CreateUser.login, IsAdmin())
async def admin_user_enter_email(message: Message, state: FSMContext):
    try:
        email = message.text
        if email:
            email = email.strip()
        await state.update_data(email = email)
        await message.answer("Почта получена!")
        await message.answer("Введите ваш пароль")
        await state.set_state(CreateUser.email)
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка во время создания пользователя, попробуйте снова", reply_markup=inline_keyboards.restart)
        await state.clear()
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error",
            source="message",
            payload="error"
        )
        return


@router.message(CreateUser.email, IsAdmin())
async def admin_user_enter_password(message: Message, state: FSMContext):
    try:
        password = message.text
        if password:
            password = password.strip()
        await state.update_data(password = password)
        await message.answer("Пароль получен!")
        data = await state.get_data()
        login = data.get("login")
        email = data.get("email")
        result = await post_user(
            telegram_id = message.from_user.id,
            login=login,
            password=password,
            churned=False,
            email=email
        )
        if result is None or not result:
            raise ValueError("Error while sending info to the server")
        await message.answer(
            "Вы успешно зарегались! Нажмите на кнопку чтоб начать диалог...",
            reply_markup=inline_keyboards.restart
        )
    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка во время создания пользователя, попробуйте снова", reply_markup=inline_keyboards.restart)
        await state.clear()
        await build_log_message(
            telegram_id=message.from_user.id,
            action="error",
            source="message",
            payload="error"
        )
        return


#===========================================================================================================================
# Создание рассылки
#===========================================================================================================================


@router.callback_query(F.data == "send_menu", IsAdmin())
async def send_main_menu_admin(callback: CallbackQuery, state: FSMContext):
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



#===========================================================================================================================
# Создание опросника
#===========================================================================================================================


@router.callback_query(F.data == "start_polling", IsAdmin())
async def start_polling_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.answer(
        "Всем действующим пользователям направлен опросник о качестве взаимодействия с ботом"
    )
    await callback.message.answer(
        "Вы можете увидеть результаты в вашем личном кабинете в дашборде"
    )
    users_data = await get_alive(telegram_id=callback.from_user.id)

    if not users_data or not isinstance(users_data, list):
        await callback.message.answer("Ошибка при рассылке опроса. попробуйте позже.", reply_markup=inline_user_keyboards.home)
        await state.clear()
        return
    tasks = []
    for user in users_data:
        user_id = user.get("telegram_id")
        tasks.extend(
            (
                bot.send_message(chat_id=user_id, text="Для улучшения качества работы мы просим вас пройти небольшой опросик (всего 3 вопроса)"),
                bot.send_message(
                    chat_id=user_id, 
                    text="Как вы оцениваете качество ответов модели?", 
                    reply_markup=inline_keyboards.grade_keyboard(
                        prefix="model_answer_grade"
                    ))
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_sends = sum(1 for r in results if not isinstance(r, TelegramAPIError))
    failed_sends = (len(results) - successful_sends)//2

    await callback.message.answer(
        f"Рассылка завершена.\n✅ Успешно: {successful_sends//2}\n❌ Ошибки: {failed_sends}",
        reply_markup=inline_keyboards.main
    )
    await state.clear()



@router.callback_query(F.data.startswith("model_answer_grade"))
async def ask_second_question(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        grade = int((callback.data.strip().split("_"))[3])
        await state.set_state(states.Grades.first)
        await state.update_data(model_grade = grade)
        await callback.message.answer(
            text="Как вы оцениваете скорость работы сервиса?", 
            reply_markup=inline_keyboards.grade_keyboard(
                prefix="service_answer_grade"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



@router.callback_query(states.Grades.first, F.data.startswith("service_answer_grade"))
async def ask_third_question(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        grade = int((callback.data.strip().split("_"))[3])
        await state.set_state(states.Grades.second)
        await state.update_data(service_grade = grade)
        await callback.message.answer(
            text="Как вы оцениваете общее удобство сервиса?", 
            reply_markup=inline_keyboards.grade_keyboard(
                prefix="convinience_grade"
        ))
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data.startswith("convinience_grade"))
async def get_message_results(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        convenience_grade = int((callback.data.strip().split("_"))[2])
        await state.update_data(convenience_grade = convenience_grade)
        await state.set_state(states.Grades.finish)
        await callback.message.answer(
            text="Спасибо вам большое!\n\nМы обязательно станем лучше!\n\nДержите котика!!!", 
            reply_markup=inline_keyboards.home
        )
        await get_cat_photo(
            bot = bot,
            chat_id = callback.from_user.id
        )
        await callback.message.answer(
            "Можете нас похвалить, поругать или предложить. А можете и ничего не делать!", 
            reply_markup=inline_keyboards.main_special
        )
        await state.set_state(states.Grades.finish)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.Grades.finish)
async def summarize_results(message: Message, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        feedback = message.text
        service_grade = data.get("service_grade")
        model_grade = data.get("model_grade")
        convenience_grade = data.get("convenience_grade")
        result = await post_poll_result(
            telegram_id=message.from_user.id,
            service_grade=service_grade,
            model_grade=model_grade,
            overall_grade=convenience_grade,
            message=feedback
        )
        if result is None:
            logging.error("Error while sending the result to the server")
        await message.answer(
            "Спасибо вам большое! Держите еще котика 🐈"
        )
        await get_cat_photo(
            bot = bot,
            chat_id = message.from_user.id
        )
        await message.answer(
            "Можем снова приступать к работе!",
            reply_markup=inline_keyboards.main
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
    finally:
        await state.clear()


@router.callback_query(F.data == "exit_hysteria")
async def get_callback_results(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        service_grade = data.get("service_grade")
        model_grade = data.get("model_grade")
        convenience_grade = data.get("convenience_grade")
        result = await post_poll_result(
            telegram_id=callback.message.from_user.id,
            service_grade=service_grade,
            model_grade=model_grade,
            overall_grade=convenience_grade,
        )
        if result is None:
            logging.error("Error while sending the result to the server")
        await callback.message.answer(
            "Можем снова приступать к работе!",
            reply_markup=inline_keyboards.main
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()