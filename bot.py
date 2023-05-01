from aiogram import Dispatcher, Bot, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InputFile

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageIsTooLong

from module_weather import get_weather, get_forecast_weather
from module_cat import get_cat_photo
from config2 import TOKEN_API, OPEN_WEATHER_TOKEN


bot = Bot(token=TOKEN_API)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
cb = CallbackData('ikb', 'command')

class ProfileStatesGroup(StatesGroup):
    weather = State()
    current_weather = State()
    forecast_weather = State()
    cat = State()

############## Клавиатуры ###################################################
# Главное меню
def main_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Погода", callback_data=cb.new('weather'))],
        [InlineKeyboardButton(text="Посмотреть котика", callback_data=cb.new('cat'))]
])

    return ikb

# Отмена для возврата в главное меню
def cancel_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в главное меню", callback_data=cb.new('cancel'))]
])
    return ikb

# Погода
def weather_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Текущая погода", callback_data=cb.new('weather_current')),
         InlineKeyboardButton(text="С интервалом в три часа", callback_data=cb.new('forecast_weather'))],
        [InlineKeyboardButton(text="Вернуться в главное меню", callback_data=cb.new('cancel'))]
])
    return ikb

# Котики
def cat_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фото котика", callback_data=cb.new('cat'))],
        [InlineKeyboardButton(text="Вернуться в главное меню", callback_data=cb.new('cancel'))]
])
    return ikb
#############################################################################


############## Обработчики ##################################################
# Обработка команды 'start'
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(text="Добро пожаловать!",
                         reply_markup=main_ikb())

# Обработка команды 'cancel'
@dp.message_handler(commands=['cancel'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(text="Добро пожаловать!",
                         reply_markup=main_ikb())

# Обработка callback 'cancel' для всех состояний
@dp.callback_query_handler(cb.filter(command='cancel'), state='*')
async def cat_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.answer(text="Добро пожаловать!", reply_markup=main_ikb())

# Погода
@dp.callback_query_handler(cb.filter(command='weather'), state='*')
async def ikb_cb_weather(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await ProfileStatesGroup.weather.set() # установили состояние погоды
    await callback.message.edit_text("Выберите необходимый период", reply_markup=weather_ikb())

# Текущая погода
@dp.callback_query_handler(cb.filter(), state=ProfileStatesGroup.weather)
async def ikb_cb_weather(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data['command'] == 'weather_current':
        await ProfileStatesGroup.current_weather.set()  # установили состояние Текущей погоды
        await callback.message.edit_text("Напишите название города", reply_markup=cancel_ikb())
    elif callback_data['command'] == 'forecast_weather':
        await ProfileStatesGroup.forecast_weather.set()  # установили состояние Прогноза погоды
        await callback.message.edit_text("Укажите название города и количество 3-часовых интервалов (до 40), разделив их пробелом. В случае, если интервал не указан явно, применяется значение по умолчанию — 2 интервала.", reply_markup=cancel_ikb())

# Вызов модуля текущей погоды
@dp.message_handler(state=ProfileStatesGroup.current_weather)
async def weather_city(message: types.Message):
    await message.answer(text=get_weather(message.text, OPEN_WEATHER_TOKEN), reply_markup=cancel_ikb(), parse_mode='html')

# Вызов модуля прогноза погоды
@dp.message_handler(state=ProfileStatesGroup.forecast_weather)
async def weather_city(message: types.Message):
    # если есть число, подставляем в количество итераций по 3 часа, если нет то по умолчанию 1 итерация
    text_part = message.text.strip().split()
    if text_part[-1].isdigit():
        hours_count = int(text_part[-1])
    else:
        hours_count = 2

    # если последнее слово это число, то оно убирается
    if text_part[-1].isdigit():
        city = ' '.join(text_part[:-1])
    else:
        city = message.text
    
    text = get_forecast_weather(city, OPEN_WEATHER_TOKEN, count=hours_count)
    MAX_MESSAGE_LENGTH = 4096
    chunks = [text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
    for chunk in chunks:
        try:
            await message.answer(text=chunk, reply_markup=cancel_ikb(), parse_mode='html')
        except MessageIsTooLong:
            continue

# Котики
@dp.callback_query_handler(cb.filter(command='cat'), state='*')
async def ikb_cb_cat(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await ProfileStatesGroup.cat.set() # установили состояние котика
    await callback.answer(text="Вскоре на экране появится очаровательный котик")
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_photo(chat_id=callback.message.chat.id, photo=InputFile.from_url(await get_cat_photo()), reply_markup=cat_ikb())

#############################################################################


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True)