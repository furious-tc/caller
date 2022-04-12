from aiogram.dispatcher.filters.state import State, StatesGroup


class StateRequest(StatesGroup):
    request = State()


class StateAnswer(StatesGroup):
    answer = State()

