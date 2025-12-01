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
from app.utils.unit_handlers import analyze_unit_economics

from app.utils.reaction_handler import ReactionManager
from app.requests.post.email import send_zip_email_with_auth
reactioner = ReactionManager()

#========================================================================================================================================================================
#========================================================================================================================================================================
# UNIT ECONOMICS BLOCK
#========================================================================================================================================================================
#========================================================================================================================================================================
def safe_float_convert(value: str, min_val=None, max_val=None):
    """Безопасное преобразование строки в float с проверкой диапазона"""
    try:
        value = value.replace(',', '.')
        result = float(value)
        
        if min_val is not None and result < min_val:
            raise ValueError(f"Значение должно быть не меньше {min_val}")
        if max_val is not None and result > max_val:
            raise ValueError(f"Значение должно быть не больше {max_val}")
        
        return result
    except ValueError as e:
        raise
    except Exception:
        raise ValueError("Некорректное число")


def safe_int_convert(value: str, min_val=None, max_val=None):
    """Безопасное преобразование строки в int с проверкой диапазона"""
    try:
        result = int(value)
        
        if min_val is not None and result < min_val:
            raise ValueError(f"Значение должно быть не меньше {min_val}")
        if max_val is not None and result > max_val:
            raise ValueError(f"Значение должно быть не больше {max_val}")
        
        return result
    except ValueError as e:
        raise
    except Exception:
        raise ValueError("Некорректное целое число")


async def send_economics_results(res, byte_data, message, bot):
    """
    Отправка всех результатов анализа пользователю в боте
    
    Args:
        res: UnitEconomicsResult (результаты анализа)
        byte_data: io.BytesIO (ZIP архив)
        message: Message объект
        bot: Bot объект
    """
    try:
        summary_text = format_telegram_summary(res)
        await message.answer(summary_text, parse_mode='Markdown')
        
        if 'basic_report.xlsx' in res.files:
            excel_buffer = res.files['basic_report.xlsx']
            excel_buffer.seek(0)
            
            await bot.send_document(
                chat_id=message.chat.id,
                document=BufferedInputFile(
                    file=excel_buffer.getvalue(),
                    filename='Основные_метрики.xlsx'
                ),
                caption="📊 Основные метрики в Excel"
            )
        
        if 'bep_chart.png' in res.files:
            chart_buffer = res.files['bep_chart.png']
            chart_buffer.seek(0)
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(
                    file=chart_buffer.getvalue(),
                    filename='bep_chart.png'
                ),
                caption="🎯 График точки безубыточности"
            )

        if 'cohort_accumulated_profit.png.png' in res.files:
            chart_buffer = res.files['cohort_accumulated_profit.png.png']
            chart_buffer.seek(0)
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(
                    file=chart_buffer.getvalue(),
                    filename='cohort_accumulated_profit.png.png'
                ),
                caption="🎯 График накопленной прибыли"
            )

        if 'cohort_audience_growth.png.png' in res.files:
            chart_buffer = res.files['cohort_audience_growth.png.png']
            chart_buffer.seek(0)
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(
                    file=chart_buffer.getvalue(),
                    filename='cohort_audience_growth.png.png'
                ),
                caption="🎯 График роста аудитории"
            )

        if 'cohort_profit_dynamics.png.png' in res.files:
            chart_buffer = res.files['cohort_profit_dynamics.png.png']
            chart_buffer.seek(0)
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(
                    file=chart_buffer.getvalue(),
                    filename='cohort_profit_dynamics.png.png'
                ),
                caption="🎯 График изменения прибыли"
            )

        if 'cohort_analysis.xlsx' in res.files:
            cohort_buffer = res.files['cohort_analysis.xlsx']
            cohort_buffer.seek(0)
            
            await bot.send_document(
                chat_id=message.chat.id,
                document=BufferedInputFile(
                    file=cohort_buffer.getvalue(),
                    filename='Когортный_анализ.xlsx'
                ),
                caption="📈 Когортный анализ на 24 периода"
            )
        
        byte_data.seek(0)
        await bot.send_document(
            chat_id=message.chat.id,
            document=BufferedInputFile(
                file=byte_data.getvalue(),
                filename=f'Полный_отчет_{message.chat.id}.zip'
            ),
            caption="🗜️ Полный архив со всеми файлами"
        )
        
        if 'summary_report.txt' in res.files:
            txt_buffer = res.files['summary_report.txt']
            txt_buffer.seek(0)
            report_text = txt_buffer.read().decode('utf-8')
            if len(report_text) > 4000:
                for i in range(0, len(report_text), 4000):
                    await message.answer(f"📄 Отчет (часть {i//4000 + 1}):\n```\n{report_text[i:i+4000]}\n```", parse_mode='Markdown')
            else:
                await message.answer(f"📄 Текстовый отчет:\n```\n{report_text}\n```", parse_mode='Markdown')
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке файлов: {str(e)}")


def format_telegram_summary(res):
    """Форматирует сводку для Telegram"""
    br = res.basic_report
    
    return f"""
📊 *ОТЧЕТ ПО ЮНИТ-ЭКОНОМИКЕ*

*Основные метрики:*
• Продукт: {br.get('name', 'N/A')}
• Пользователи: {br.get('users', 0):,.0f}
• Клиенты: {br.get('customers', 0):,.0f}
• Конверсия: {br.get('C1', 0):.1%}
• ARPU: ${br.get('ARPU', 0):,.2f}
• CAC: ${br.get('CAC', 0):,.2f}
• LTV: ${br.get('LTV', 0):,.2f}
• ROI: {br.get('ROI', 0):.1f}%
• Прибыль: ${br.get('Profit', 0):,.2f}

🎯 *Точка безубыточности:*
• BEP: {res.bep_analysis.get('BEP_units_rounded', 0):,.0f} юнитов
• FC: ${res.bep_analysis.get('FC', 0):,.2f}
• UCM: ${res.bep_analysis.get('UCM', 0):,.2f}

📈 *Статус:* {"✅ Рентабельно" if br.get('UCM', 0) > 0 else "⚠️ Нерентабельно"}

_Отправляю файлы с детальным анализом..._
"""

import re

@router.callback_query(F.data == "unit_menu")
async def catalogue_callback_admin(callback: CallbackQuery, state:FSMContext):
    try:
        await callback.answer()
        await state.clear()
        await callback.message.answer("Введите название проекта")
        await state.set_state(Unit.name)
    except Exception as e:
        logging.exception(e)
        await callback.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.name)
async def post_enter_name_admin(message: Message, state: FSMContext, bot:Bot):
    try:
        name = message.text.strip()
        if not name or len(name) < 2 or len(name) > 100:
            await message.answer("Введите валидное имя проекта (от 2 до 100 символов)")
            return
        if re.search(r'[<>\\/]', name):
            await message.answer("Имя проекта содержит запрещенные символы")
            return
        await state.update_data(name=name)
        await state.set_state(Unit.users)
        await reactioner.add_reaction(bot=bot, message=message, emoji="🤝")
        await message.answer("Введите количество привлеченных пользователей")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.users)
async def post_enter_description_admin(message: Message, state: FSMContext, bot:Bot):
    try:
        users = message.text.strip()
        if not users.isdigit():
            await message.answer("Введите целое положительное число пользователей")
            return
        users_int = int(users)
        if users_int <= 0:
            await message.answer("Количество пользователей должно быть больше 0")
            return
        if users_int > 1000000000:
            await message.answer("Слишком большое количество пользователей")
            return
        await state.update_data(users=users_int)
        await state.set_state(Unit.customers)
        await reactioner.add_reaction(bot=bot, message=message, emoji="❤️‍🔥")
        await message.answer("Введите количество полученных клиентов")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.customers)
async def post_enter_price_admin(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        customers = message.text.strip()
        
        if not customers.isdigit():
            await message.answer("Введите целое положительное число клиентов")
            return
        
        customers_int = int(customers)
        if customers_int <= 0:
            await message.answer("Количество клиентов должно быть больше 0")
            return
        
        if customers_int > 1000000000:
            await message.answer("Слишком большое количество клиентов")
            return
        
        users = data.get("users")
        if users is not None and customers_int > users:
            await message.answer(f"Клиентов ({customers_int}) не может быть больше чем пользователей ({users})")
            return
        
        await state.update_data(customers=customers_int)
        await state.set_state(Unit.AVP)
        await message.answer("Введите AVP (Average Value of Payment - средний чек)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.message(Unit.AVP)
async def post_enter_country_admin(message: Message, state: FSMContext, bot:Bot):
    try:
        AVP = message.text.strip()
        if not AVP:
            await message.answer("Введите число AVP")
            return
        
        try:
            avp_float = safe_float_convert(AVP, min_val=0.01, max_val=10000000)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число AVP (например: 50 или 29.99)")
            return
        
        await state.update_data(AVP=avp_float)
        await state.set_state(Unit.APC)
        await reactioner.add_reaction(bot=bot, message=message, emoji="🔥")
        await message.answer("Введите APC (Average Purchase Count - кол-во покупок на клиента за рассчетный период)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.APC)
async def post_enter_apc_admin(message: Message, state: FSMContext, bot:Bot):
    try:
        APC = message.text.strip()
        if not APC:
            await message.answer("Введите число APC")
            return
        
        try:
            apc_float = safe_float_convert(APC, min_val=0.01, max_val=1000)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число APC (например: 2 или 1.5)")
            return
        
        await state.update_data(APC=apc_float)
        await state.set_state(Unit.TMS)
        await reactioner.add_reaction(bot=bot, message=message, emoji="🔥")
        await message.answer("Введите TMS (Total Marketing Spends)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.TMS)
async def post_enter_tms_admin(message: Message, state: FSMContext):
    try:
        TMS = message.text.strip()
        if not TMS:
            await message.answer("Введите число TMS")
            return
        
        try:
            tms_float = safe_float_convert(TMS, min_val=0, max_val=1000000000)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число TMS (например: 5000 или 10000.50)")
            return
        
        await state.update_data(TMS=tms_float)
        await state.set_state(Unit.COGS)
        await message.answer("Введите COGS (Cost of goods sold)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.COGS)
async def post_enter_rr_admin(message: Message, state: FSMContext):
    try:
        COGS = message.text.strip()
        if not COGS:
            await message.answer("Введите число COGS")
            return
        
        try:
            cogs_float = safe_float_convert(COGS, min_val=0, max_val=10000000)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число COGS (например: 15 или 10.50)")
            return
        
        data = await state.get_data()
        avp = data.get('AVP')
        if avp is not None and cogs_float > avp:
            await message.answer(f"COGS ({cogs_float}) не может быть больше AVP ({avp})")
            return
            
        await state.update_data(COGS=cogs_float)
        await state.set_state(Unit.RR)
        await message.answer("Введите RR (Retention Rate) от 0 до 1 (например: 0.8 для 80%)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.RR)
async def post_enter_agr_admin(message: Message, state: FSMContext):
    try:
        RR = message.text.strip()
        if not RR:
            await message.answer("Введите число RR")
            return
        
        try:
            rr_float = safe_float_convert(RR, min_val=0, max_val=1)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число RR от 0 до 1 (например: 0.8 или 0.95)")
            return
        
        await state.update_data(RR=rr_float)
        await state.set_state(Unit.AGR)
        await message.answer("Введите AGR (Audience Growth Rate) от 0 до 1 (например: 0.1 для 10%)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.AGR)
async def post_enter_cogs_admin(message: Message, state: FSMContext, bot:Bot):
    try:
        AGR = message.text.strip()
        if not AGR:
            await message.answer("Введите число AGR")
            return
        
        try:
            agr_float = safe_float_convert(AGR, min_val=0, max_val=1)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число AGR от 0 до 1 (например: 0.1 или 0.05)")
            return
        
        await reactioner.add_reaction(bot=bot, message=message, emoji="🎉")
        await state.update_data(AGR=agr_float)
        await state.set_state(Unit.COGS1s)
        await message.answer("Введите COGS1s (Cost of goods sold first sale)")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.COGS1s)
async def post_enter_cogs1s_admin(message: Message, state: FSMContext):
    try:
        COGS1s = message.text.strip()
        if not COGS1s:
            await message.answer("Введите число COGS1s")
            return
        
        try:
            cogs1s_float = safe_float_convert(COGS1s, min_val=0, max_val=1000000)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число COGS1s (например: 5 или 3.50)")
            return
        
        await state.update_data(COGS1s=cogs1s_float)
        await state.set_state(Unit.FC)
        await message.answer("Введите FC (Fixed Costs) - постоянные издержки")
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(Unit.FC)
async def post_enter_fc_admin(message: Message, state: FSMContext, bot:Bot):
    try:
        FC = message.text.strip()
        if not FC:
            await message.answer("Введите число FC")
            return
        
        try:
            fc_float = safe_float_convert(FC, min_val=0, max_val=1000000000)
        except ValueError as e:
            await message.answer(f"Ошибка: {str(e)}. Введите число FC (например: 10000 или 15000.50)")
            return
        
        await reactioner.add_reaction(bot=bot, message=message, emoji="✍️")
        await state.update_data(FC=fc_float)
        data = await state.get_data()

        if not data:
            await message.answer("Ошибка при создании юнита", reply_markup=inline_keyboards.main)
            return

        msg = (
            f"🧩 **Модель успешно создана:**\n\n"
            f"**Название:** `{data.get('name')}`\n"
            f"**Пользователи:** `{data.get('users')}`\n"
            f"**Клиенты:** `{data.get('customers')}`\n"
            f"**AVP:** `{data.get('AVP')}`\n"
            f"**APC:** `{data.get('APC')}`\n"
            f"**ТМS:** `{data.get('TMS')}`\n"
            f"**СОGS:** `{data.get('COGS')}`\n"
            f"**СОGS1s:** `{data.get('COGS1s')}`\n"
            f"**FC:** `{data.get('FC')}`"
        )
        
        await message.answer(msg, parse_mode='Markdown')
        
        try:
            res, zip_buffer = analyze_unit_economics(data=data)
            
            await send_economics_results(res, zip_buffer, message, bot)
            
            await state.update_data(zip_file=zip_buffer)
            
            await message.answer(
                "Вы хотите получить результат на почту?", 
                reply_markup=await inline_keyboards.email_choice(telegram_id=message.from_user.id)
            )
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при анализе данных: {str(e)}", reply_markup=inline_keyboards.main)
            await state.clear()
    except Exception as e:
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()

@router.callback_query(F.data == "email_deny")
async def email_deny_admin(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer(
            "Понял, что будем делать дальше?", 
            reply_markup=inline_keyboards.main
        )
        await state.clear()
    except Exception as e:
        logging.exception(e)
        await callback.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data.startswith("email_account"))
async def email_accept_account(callback: CallbackQuery, state: FSMContext):
    try:
        user = await get_users(
            telegram_id=callback.from_user.id,
            tg_id=callback.from_user.id
        )
        
        data = await state.get_data()
        
        if not user or not user.get("email") or not data.get("zip_file"):
            await callback.message.answer("🥲 Возникла проблема при получении данных...")
            await callback.message.answer(
                "Можем попробовать еще раз...", 
                reply_markup=await inline_keyboards.email_choice(telegram_id=callback.from_user.id)
            )
            return
        
        zip_buffer = data.get("zip_file")
        zip_buffer.seek(0)
        
        res = await send_zip_email_with_auth(
            zip_buffer=zip_buffer,
            receiver_email=user.get("email"),
            telegram_id=str(callback.from_user.id),
            subject=f"Отчет по юнит-экономике",
            text_message=f"Отчет по анализу юнит-экономики",
            filename=f"unit_economics_report.zip"
        )
        
        if res and res.get("error"):
            await callback.message.answer("🥲 Возникла проблема при отправке...")
            await callback.message.answer(
                "Можем попробовать еще раз...", 
                reply_markup=await inline_keyboards.email_choice(telegram_id=callback.from_user.id)
            )
        else:
            await callback.message.answer("🎉 Сообщение успешно отправлено!!!", reply_markup=inline_keyboards.main)
            await state.clear()
            
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}", reply_markup=inline_keyboards.main)
        logging.exception(e)
        await callback.message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.callback_query(F.data.startswith("email_custom"))
async def email_custom_accept_get(callback: CallbackQuery, state: FSMContext):
    try:
        await state.set_state(states.SendReport.handle)
        await callback.message.answer("Напишите вашу почту, на которую отправится отчет")
    except Exception as e:
        logging.exception(e)
        await callback.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()


@router.message(states.SendReport.handle)
async def email_custom_accept(message: Message, state: FSMContext):
    try:
        email = message.text.strip()
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            await message.answer("❌ Введите корректный email адрес")
            return
        
        data = await state.get_data()
        
        if not data.get("zip_file"):
            await message.answer("🥲 Архив не найден. Пожалуйста, создайте отчет заново.")
            await state.clear()
            return
        
        zip_buffer = data.get("zip_file")
        if not isinstance(zip_buffer, BytesIO):
            raise ValueError("Ошибка получения буффера из FSM")
        zip_buffer.seek(0)
        
        res = await send_zip_email_with_auth(
            zip_buffer=zip_buffer,
            receiver_email=email,
            telegram_id=str(message.from_user.id),
            subject="Отчет по юнит-экономике",
            text_message="Отчет по анализу юнит-экономики",
            filename=f"unit_economics_report_{message.from_user.id}.zip"
        )
        
        if res and res.get("error"):
            await message.answer("🥲 Возникла проблема при отправке...")
            await message.answer(
                "Можем попробовать еще раз...", 
                reply_markup=await inline_keyboards.email_choice(telegram_id=message.from_user.id)
            )
        else:
            await message.answer("🎉 Сообщение успешно отправлено!!!", reply_markup=await inline_keyboards.email_choice(telegram_id=message.from_user.id))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=inline_keyboards.main)
        logging.exception(e)
        await message.answer("Извините, бот немножко устал, попробуйте позже 😢", reply_markup=inline_keyboards.home)
        await state.clear()
