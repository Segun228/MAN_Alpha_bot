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


class ChatModelAsk(StatesGroup):
    start = State()
    first = State()
    second = State()
    third = State()
    finish = State()
    handle = State()

class SummarizeModelAsk(StatesGroup):
    start = State()
    first = State()
    second = State()
    third = State()
    finish = State()
    handle = State()

class DocumentModelAsk(StatesGroup):
    start = State()
    first = State()
    second = State()
    third = State()
    finish = State()
    handle = State()


class AnalyserModelAsk(StatesGroup):
    start = State()
    first = State()
    second = State()
    third = State()
    finish = State()
    handle = State()


class CreateBusiness(StatesGroup):
    start = State()
    name = State()
    description = State()
    username = State()
    email = State()
    password = State()
    churned = State()
    is_admin = State()



class EditBusiness(StatesGroup):
    start = State()
    name = State()
    description = State()
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


class Grades(StatesGroup):
    start = State()
    finish = State()
    first = State()
    second = State()
    third = State()

