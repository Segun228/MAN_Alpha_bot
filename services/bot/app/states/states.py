from aiogram.fsm.state import StatesGroup, State

class Send(StatesGroup):
    handle = State()
    message = State()

class Distribution(StatesGroup):
    handle_distribution = State()
    handle_edit_distribution = State()
    name = State()
    distribution_type = State()
    params = State()
    description = State()
    edit_distribution = State()
    distribution_id = State()

class DistributionEdit(StatesGroup):
    handle_distribution = State()
    handle_edit_distribution = State()
    name = State()
    distribution_type = State()
    params = State()
    description = State()
    edit_distribution = State()
    distribution_id = State()

class Dataset(StatesGroup):
    handle_dataset = State()
    handle_edit_dataset = State()
    name = State()
    file = State()


class DatasetEdit(StatesGroup):
    handle_dataset = State()
    handle_edit_dataset = State()
    name = State()
    file = State()


class Probability(StatesGroup):
    probability = State()


class Interval(StatesGroup):
    interval = State()


class Sample(StatesGroup):
    sample = State()


class Quantile(StatesGroup):
    quantile = State()


class Percentile(StatesGroup):
    percentile = State()

class File(StatesGroup):
    waiting_for_file = State()
    waiting_for_name = State()
    waiting_for_replace_file = State()


class Errors(StatesGroup):
    handle_errors = State()
    alpha = State()


class Groups(StatesGroup):
    handle = State()
    test = State()
    controle = State()


class SampleSize(StatesGroup):
    mde = State()


class Confirm(StatesGroup):
    bundle = State()
    confirmed = State()


class Bootstrap(StatesGroup):
    iterations = State()
    confirmed = State()


class Cuped(StatesGroup):
    hostory_col = State()
    waiting_for_history_file = State()
    select_history_column = State()


class Cupac(StatesGroup):
    waiting_for_history_file = State()
    select_target_metric = State()
    select_feature_columns = State()


class CreateModel(StatesGroup):
    start_create = State()
    type = State()
    name = State()
    description = State()
    target = State()
    file = State()
    features = State()


class PredictModel(StatesGroup):
    start_predict = State()
    get_file = State()
    finish_predict = State()


class FitModel(StatesGroup):
    start_fit = State()
    get_fit_file = State()
    finish_fit = State()


class RefitModel(StatesGroup):
    confirm = State()
    start_refit = State()
    get_refit_file = State()
    finish_refit = State()


class DeleteModel(StatesGroup):
    confirm = State()
    handle = State()


class PutModel(StatesGroup):
    confirm = State()
    handle = State()
    type = State()
    name = State()
    description = State()
    target = State()
    file = State()


class GenerateSample(StatesGroup):
    start = State()
    features = State()
    meaning = State()
    noise = State()