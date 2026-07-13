from aiogram.fsm.state import StatesGroup, State


class PurchaseStates(StatesGroup):
    choosing_package = State()
    entering_discount_code = State()
    entering_service_name = State()
    confirming_price = State()
    waiting_receipt = State()


class SupportStates(StatesGroup):
    waiting_message = State()
