from app.handlers.router import llm_router as router
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
from app.requests.models.post_document_model import post_document_model, post_conv_model
from app.requests.models.post_summarize_model import post_summarize_model
from app.requests.models.post_idea_model import post_idea_model
from app.requests.models.post_analysis_model import post_analysis_model
from app.utils.reaction_handler import ReactionManager
from app.middlewares.history import BotReplyLogger, UserMessageLogger
from app.requests.post.post_audio import send_audio
replier = BotReplyLogger()
requester = UserMessageLogger()
reactioner = ReactionManager()


import re

def replace_bold_only(text: str) -> str:
    """
    Заменяет только **жирный** на <b>жирный</b>
    Остальной текст остается как есть
    """
    if not text:
        return text
    
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    return text

def safe_bold_replace(text: str) -> str:
    """
    Безопасная замена с проверкой баланса тегов
    """
    try:
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;') 
        text = text.replace('>', '&gt;')
        
        html_text = replace_bold_only(text)
        open_tags = html_text.count('<b>')
        close_tags = html_text.count('</b>')
        
        if open_tags != close_tags:
            logging.warning("Несбалансированные <b> теги, возвращаем оригинал")
            return text
            
        return html_text
        
    except Exception as e:
        logging.error(f"Ошибка замены жирного текста: {e}")
        return text



def escape_markdown_v2(text: str, version: int = 2) -> str:
    if not text:
        return ""
    if version == 1:
        escape_chars = r'_*`['
    else:
        escape_chars = r'_*[]()~`>#+-=|{}.!'
    pattern = r'([{}])'.format(re.escape(escape_chars))
    escaped_text = re.sub(pattern, r'\\\1', text)
    return escaped_text

#===========================================================================================================================
# Conversation
#===========================================================================================================================


@router.callback_query(F.data.startswith("conversation"))
async def get_conversation_start(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "Опишите вашу ситуацию на переговорах, чем подробнее описание - тем лучше качество ответа",
        )
        await callback.message.answer(
            "Операция очень тяжелая, при ошибке нажмите 'Повторить'",
        )
        await state.set_state(states.Conv.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.message(states.Conv.start)
async def ask_Conv_question(message: Message, state: FSMContext, bot:Bot):
    try:
        user_question = message.text
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🔥"
        )
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        
        await message.answer("Я вас понял, дайте секунду подумать...")
        await state.update_data(user_question=user_question)
        
        result = await post_conv_model(
            telegram_id=message.from_user.id,
            text=user_question
        )
        logging.error(result)
        if result is None:
            await message.answer(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
        if not isinstance(result, dict):
            await message.answer(
                safe_bold_replace(result),
                reply_markup=inline_keyboards.main,
                parse_mode="html"
            )
            await requester.log_user_message(
                telegram_id=message.from_user.id,
                text=user_question,
                message_id=message.message_id,
            )
            await replier.log_bot_response(
                telegram_id=message.from_user.id,
                text=result,
            )
        else:
            raise Exception("Error while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await message.answer(
            "Извините, бот немножко устал, попробуйте позже 😢", 
            reply_markup=inline_keyboards.retry_keyboard
        )
        await state.set_state(states.Lawyer.start)


@router.callback_query(F.data == "retry_question", states.Conv.start)
async def retry_question_conv(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Повторяю запрос...")
        state_data = await state.get_data()
        user_question = state_data.get('user_question')
        
        if not user_question:
            await callback.message.answer(
                "Не удалось найти предыдущий вопрос. Пожалуйста, задайте вопрос заново.",
                reply_markup=inline_keyboards.home
            )
            await state.clear()
            return
        await callback.message.edit_text("Повторяю запрос, секунду...")
        result = await post_conv_model(
            telegram_id=callback.from_user.id,
            text=user_question
        )
        if result is None:
            await callback.message.edit_text(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
            
        if not isinstance(result, dict):
            await callback.message.edit_text(
                safe_bold_replace(result),
                reply_markup=inline_keyboards.main,
                parse_mode='html'
            )
            await requester.log_user_message(
                telegram_id=callback.from_user.id,
                text=user_question,
                message_id=callback.from_user.id,
            )
            await replier.log_bot_response(
                telegram_id=callback.from_user.id,
                text=result
            )
        else:
            raise Exception("eeror while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)

        await callback.message.edit_text(
            "Снова произошла ошибка. Попробовать еще раз?",
            reply_markup=inline_keyboards.retry_keyboard
        )


#===========================================================================================================================
# Lawyer
#===========================================================================================================================


@router.callback_query(F.data == "personal_lawyer")
async def get_justice_menu(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "Подробно опишите интересующий вас вопрос боту. Здесь вам необходимо описать его ОЧЕНЬ точно, так как бот может не понять вольностей интерпритации",
        )
        await callback.message.answer(
            "Операция очень тяжелая, при ошибке нажмите 'Повторить'",
        )
        await state.set_state(states.Lawyer.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.message(states.Lawyer.start)
async def ask_lawyer_question(message: Message, state: FSMContext, bot:Bot):
    try:
        user_question = message.text
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🔥"
        )
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        
        await message.answer("Я вас понял, дайте секунду подумать...")
        await state.update_data(user_question=user_question)
        
        result = await post_document_model(
            telegram_id=message.from_user.id,
            text=user_question
        )
        
        if result is None:
            await message.answer(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
        if not isinstance(result, dict):
            await message.answer(
                safe_bold_replace(result),
                reply_markup=inline_keyboards.main,
                parse_mode="html"
            )
            await requester.log_user_message(
                telegram_id=message.from_user.id,
                text=user_question,
                message_id=message.message_id,
            )
            await replier.log_bot_response(
                telegram_id=message.from_user.id,
                text=result,
            )
        else:
            raise Exception("Error while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await message.answer(
            "Извините, бот немножко устал, попробуйте позже 😢", 
            reply_markup=inline_keyboards.retry_keyboard
        )
        await state.set_state(states.Lawyer.start)


@router.callback_query(F.data == "retry_question", states.Lawyer.start)
async def retry_question(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Повторяю запрос...")
        state_data = await state.get_data()
        user_question = state_data.get('user_question')
        
        if not user_question:
            await callback.message.answer(
                "Не удалось найти предыдущий вопрос. Пожалуйста, задайте вопрос заново.",
                reply_markup=inline_keyboards.home
            )
            await state.clear()
            return
        await callback.message.edit_text("Повторяю запрос, секунду...")
        result = await post_document_model(
            telegram_id=callback.from_user.id,
            text=user_question
        )
        if result is None:
            await callback.message.edit_text(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
            
        if not isinstance(result, dict):
            await callback.message.edit_text(
                safe_bold_replace(result),
                reply_markup=inline_keyboards.main,
                parse_mode='html'
            )
            await requester.log_user_message(
                telegram_id=callback.from_user.id,
                text=user_question,
                message_id=callback.from_user.id,
            )
            await replier.log_bot_response(
                telegram_id=callback.from_user.id,
                text=result
            )
        else:
            raise Exception("eeror while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)

        await callback.message.edit_text(
            "Снова произошла ошибка. Попробовать еще раз?",
            reply_markup=inline_keyboards.retry_keyboard
        )

#===========================================================================================================================
# Idea Generation
#===========================================================================================================================

@router.callback_query(F.data == "idea_generation")
async def generate_idea_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer("Пожалуйста, опишите ваш вопрос или идею для анализа:")
        await state.set_state(states.Idea.awaiting_question)
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        data = await state.get_data()
        question = data.get("question")
        if not question:
            await callback.message.answer("Извините, бот забыл про какой бизнес мы говорили 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            return
        await callback.message.answer("Ассистент думает, подождите пожалуйста...")
        response = await post_idea_model(
            telegram_id=callback.from_user.id,
            text=question,
        )
        if not response:
            await callback.message.answer("Модель не смогла дать внятного ответа, попробуйте переформулировать...", reply_markup=inline_keyboards.home)
            return
        await callback.message.answer(
            safe_bold_replace(str(response)),
            reply_markup= inline_keyboards.main,
            parse_mode='html'
        )
        await requester.log_user_message(
            telegram_id=callback.from_user.id,
            text=question,
            message_id=callback.from_user.id,
            business_id=None
        )
        await replier.log_bot_response(
            telegram_id=callback.from_user.id,
            text=str(response),
            business_id = None
        )
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()
#===========================================================================================================================
# Summarise
#===========================================================================================================================


@router.callback_query(F.data == "information_structure")
async def get_information_structure(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "напишите информацию для структурирования боту",
        )
        await state.set_state(states.Summarizer.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.Summarizer.start)
async def summarizer_send_request(message:Message, state:FSMContext, bot:Bot):
    try:
        user_question = message.text
        await state.update_data(
            user_question = user_question
        )
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        await message.answer("Я вас понял, дайте секунду сформулировать...")
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="✍️"
        )
        result = await post_summarize_model(
            telegram_id = message.from_user.id,
            text = user_question
        )
        if result is None:
            await message.answer(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
        if not isinstance(result, dict):
            await message.answer(
                safe_bold_replace(result),
                reply_markup=inline_keyboards.main,
                parse_mode='html'
            )
            await requester.log_user_message(
                telegram_id=message.from_user.id,
                text=user_question,
                message_id=message.message_id,
            )
            await replier.log_bot_response(
                telegram_id=message.from_user.id,
                text=str(result)
            )
        elif isinstance(result, dict):
            await message.answer(
                safe_bold_replace(result.get("response", "Извините, модель не смогла дать внятного ответа 😭")),
                reply_markup=inline_keyboards.main,
                parse_mode='html'
            )
            await requester.log_user_message(
                telegram_id=message.from_user.id,
                text=user_question,
                message_id=message.message_id,
            )
            await replier.log_bot_response(
                telegram_id=message.from_user.id,
                text=str(result)
            )
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await message.answer(
            "Извините, бот немножко устал, попробуйте позже 😢", 
            reply_markup=inline_keyboards.retry_keyboard
        )
        await state.set_state(states.Summarizer.start)


@router.callback_query(F.data == "retry_question", states.Summarizer.start)
async def retry_summarize_question(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("Повторяю запрос...")
        state_data = await state.get_data()
        user_question = state_data.get('user_question')
        
        if not user_question:
            await callback.message.answer(
                "Не удалось найти предыдущий вопрос. Пожалуйста, задайте вопрос заново.",
                reply_markup=inline_keyboards.home
            )
            await state.clear()
            return
        await callback.message.edit_text("Повторяю запрос, секунду...")
        result = await post_summarize_model(
            telegram_id=callback.from_user.id,
            text=user_question
        )
        if result is None:
            await callback.message.edit_text(
                "Модель не смогла дать внятного ответа, попробуйте переформулировать...", 
                reply_markup=inline_keyboards.home
            )
            return
            
        if not isinstance(result, dict):
            await callback.message.edit_text(
                safe_bold_replace(result),
                reply_markup=inline_keyboards.main,
                parse_mode='html'
            )
            await requester.log_user_message(
                telegram_id=callback.from_user.id,
                text=user_question,
                message_id=callback.from_user.id,
            )
            await replier.log_bot_response(
                telegram_id=callback.from_user.id,
                text=str(result),
            )
        else:
            raise Exception("eeror while getting te result")
        await state.clear()
        
    except Exception as e:
        logging.exception(e)

        await callback.message.edit_text(
            "Снова произошла ошибка. Попробовать еще раз?",
            reply_markup=inline_keyboards.retry_keyboard
        )


#===========================================================================================================================
# Business analytics
#===========================================================================================================================

@router.callback_query(F.data == "business_analysis")
async def get_analyzis_type(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer(
            "Какой вид анализа вы хотите провести?",
            reply_markup=inline_keyboards.business_analysis
        )
        await state.set_state(states.Summarizer.start)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


#==================
# Business analysis
#==================

@router.callback_query(F.data == "swot_start")
async def swot_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "swot")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "bmc_start")
async def bmc_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "bmc")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "cjm_start")
async def cjm_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "cjm")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data == "vpc_start")
async def vpc_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "vpc")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.callback_query(F.data == "pest_start")
async def pest_analysis(callback:CallbackQuery, state:FSMContext):
    try:
        await callback.message.answer("В подробностях опишите, что нам необходимо знать. Также, при анализе будет учтена история нашего диалога")
        await state.set_state(states.Analysys.swot)
        await state.update_data(type = "pest")
        return
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



@router.message(states.Analysys.swot)
async def analyzer_send_request(message:Message, state:FSMContext, bot:Bot):
    try:
        user_question = message.text
        if not user_question or not user_question.strip():
            await message.answer("Не могли бы вы раскрыть свой вопрос подробнее, я вас не совсем понял")
            return
        await state.update_data(
            question = user_question
        )
        await message.answer(
            "К какому из ваших проектов относится данный вопрос?",
            reply_markup=await inline_keyboards.get_precise_catalogue(telegram_id=message.from_user.id)
        )
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤔"
        )
        await state.set_state(states.Analysys.cjm)

    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()



@router.callback_query(F.data.startswith("choose_business_"), states.Analysys.cjm)
async def business_analysis_finish(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer("Я вас понял, дайте секунду проанализировать...")
        data = await state.get_data()
        analyzys_type = data.get("type")
        if not analyzys_type:
            raise ValueError("No type was saved")

        question = data.get("question")
        if not question:
            raise ValueError("No question was saved")

        business_id = int(callback.data.replace("choose_business_", ""))
        current_business = await get_business(
            telegram_id=callback.from_user.id,
            business_id=business_id
        )
        if not current_business:
            await callback.message.answer("Извините, бот не смог найти ваш бизнес 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            return
        await callback.message.answer("Ассистент думает, подождите пожалуйста...")
        response = await post_analysis_model(
            telegram_id=callback.from_user.id,
            text=question,
            description=current_business.get("description"),
            business=current_business.get("name"),
            analysis_type=analyzys_type,
            offset = 0,
            business_id = business_id
        )
        if not response:
            await callback.message.answer("Модель не смогла дать внятного ответа, попробуйте переформулировать...", reply_markup=inline_keyboards.home)
            return
        await callback.message.answer(
            safe_bold_replace(str(response)),
            reply_markup= inline_keyboards.main,
            parse_mode='html'
        )
        await requester.log_user_message(
            telegram_id=callback.from_user.id,
            text=question,
            message_id=callback.from_user.id,
            business_id=business_id
        )
        await replier.log_bot_response(
            telegram_id=callback.from_user.id,
            text=str(response),
            business_id=business_id
        )
        await state.clear()
        
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message()
async def chat_model_answer(message:Message, state:FSMContext, bot:Bot, threshold = 5):
    try:
        await message.answer("Перенаправляем ваш запрос к нашему чат-ассистенту...")
        if message.text:
            question = message.text
            if not question or len(question) < threshold:
                await message.answer("Неизвестная команда 🧐")
                await message.answer("Если вы хотите что-то спросить у чат-бота, раскройте более подробно свой вопрос пожалуйста")
        elif message.voice:
            file_id = message.voice.file_id
            file = await bot.get_file(file_id)
            byt = await bot.download_file(file.file_path)
            if not byt or byt is None:
                raise ValueError("Error while getting the file")
            audio_bytes = byt.read()
            byt.close()
            question = await send_audio(audio_bytes, telegram_id=message.from_user.id)
            if not question:
                raise ValueError("Error while getting the file")
        await state.set_state(states.ChatModelAsk.start)
        await state.update_data(question = question)
        await message.answer(
            "К какому из ваших проектов относится данный вопрос?\n\nЭто нужно нам для более точного понимания ваших потребностей...",
            reply_markup= await inline_keyboards.get_precise_catalogue(telegram_id=message.from_user.id)
        )
        await reactioner.add_reaction(
            bot=bot,
            message=message,
            emoji="🤔"
        )
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.callback_query(F.data.startswith("choose_business_"), states.ChatModelAsk.start)
async def chat_model_finish(callback:CallbackQuery, state:FSMContext):
    try:
        data = await state.get_data()
        question = data.get("question")
        if not question:
            await callback.message.answer("Извините, бот забыл про какой бизнес мы говорили 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            raise ValueError("Error while memorising the question")
        business_id = int(callback.data.strip().split("_")[2])
        current_business = await get_business(
            telegram_id=callback.from_user.id,
            business_id=business_id
        )
        if not current_business:
            await callback.message.answer("Извините, бот не смог найти ваш бизнес 🥲\n\nПроблема на нашей стороне 👨‍🔧")
            raise ValueError("Error while memorising the question")
        await callback.message.answer("Ассистент думает, подождите пожалуйста...")
        response = await post_chat_model(
            telegram_id=callback.from_user.id,
            text = question,
            description = current_business.get("description"),
            business = current_business.get("name"),
            business_id = current_business.get("id"),
            offset=5
        )
        if not response:
            await callback.message.answer("Модель не смогла дать внятного ответа, попробуйте переформулировать...", reply_markup=inline_keyboards.home)
            return
        await callback.message.answer(
            safe_bold_replace(str(response)),
            reply_markup= inline_keyboards.main,
            parse_mode='html'
        )
        await requester.log_user_message(
            telegram_id=callback.from_user.id,
            text=question,
            message_id=callback.from_user.id,
            business_id=business_id
        )
        await replier.log_bot_response(
            telegram_id=callback.from_user.id,
            text=str(response),
            business_id=business_id
        )
    except Exception as e:
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()
