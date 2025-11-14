from aiogram.fsm.state import StatesGroup, State

class Send(StatesGroup):
    handle = State()
    message = State()


class CreateUser(StatesGroup):
    start_creating = State()
    login = State()
    email = State()
    password = State()
    churned = State()
    is_admin = State()


class CreateBusiness(StatesGroup):
    username = State()
    email = State()
    password = State()
    churned = State()
    is_admin = State()


class Analysys(StatesGroup):
    swot = State()
    pest = State()
    cjm = State()
    bmc = State()
    vpc = State()


class Lawyer(StatesGroup):
    start = State()
    finish = State()


class Summarizer(StatesGroup):
    start = State()
    finish = State()
