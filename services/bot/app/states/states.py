from aiogram.fsm.state import StatesGroup, State

class Send(StatesGroup):
    handle = State()
    message = State()
