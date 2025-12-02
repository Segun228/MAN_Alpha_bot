from aiogram.fsm.state import StatesGroup, State

class Send(StatesGroup):
    handle = State()
    message = State()


class SendReport(StatesGroup):
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




class Idea(StatesGroup):
    start = State()
    finish = State()
    awaiting_question = State()


class Summarizer(StatesGroup):
    start = State()
    finish = State()


class Grades(StatesGroup):
    start = State()
    finish = State()
    first = State()
    second = State()
    third = State()



class Unit(StatesGroup):
    handle_unit = State()
    handle_edit_unit = State()
    model_set = State()
    name = State()
    users = State()
    customers = State()
    AVP = State()
    APC = State()
    TMS = State()
    COGS = State()
    COGS1s = State()
    FC = State()
    RR = State()
    AGR = State()


class UnitEdit(StatesGroup):
    handle_unit = State()
    handle_edit_unit = State()
    model_set = State()
    name = State()
    users = State()
    customers = State()
    AVP = State()
    APC = State()
    TMS = State()
    COGS = State()
    COGS1s = State()
    FC = State()


class SendNew(StatesGroup):
    handle = State()
    message = State()


class File(StatesGroup):
    waiting_for_file = State()
    waiting_for_name = State()
    waiting_for_replace_file = State()


class Cohort(StatesGroup):
    handle_unit = State()
    retention_rate = State()
    audience_growth_rate = State()

