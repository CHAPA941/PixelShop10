# Инструкция по установке и запуску:
# 1. Установите библиотеку aiogram:
#    pip install aiogram
# 2. Запустите скрипт:
#    python bot.py

from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8804500426:AAHLW6mxJZGUl4xH334xTZ-Vs6M03V1t3Ds"  # <-- ЗАМЕНИ НА СВОЙ НОВЫЙ ТОКЕН
ADMIN_ID = 2087257865

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================== СОСТОЯНИЯ FSM ==================
class SupportState(StatesGroup):
    waiting_for_message = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

class SetNickState(StatesGroup):
    waiting_for_nick = State()

class ReplyState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_reply_text = State()

class AddItemState(StatesGroup):
    waiting_for_game = State()
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_stock = State()

class EditItemState(StatesGroup):
    waiting_for_item_id = State()
    waiting_for_field = State()
    waiting_for_value = State()

class AddPromoState(StatesGroup):
    waiting_for_type = State()
    waiting_for_item = State()
    waiting_for_percent = State()
    waiting_for_code = State()

# ================== БАЗА ДАННЫХ ==================
def init_db():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS admins")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cart")
    cursor.execute("DROP TABLE IF EXISTS promos")
    cursor.execute("DROP TABLE IF EXISTS active_promos")

    cursor.execute("""
    CREATE TABLE items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        game TEXT,
        category TEXT,
        name TEXT,
        description TEXT,
        price_stars INTEGER,
        stock INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        admin_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE admins (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE users (
        telegram_id INTEGER PRIMARY KEY,
        roblox_nick TEXT,
        discount_percent INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE cart (
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER DEFAULT 1,
        PRIMARY KEY (user_id, item_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE promos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        type TEXT,
        value INTEGER,
        discount_percent INTEGER,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE active_promos (
        user_id INTEGER,
        promo_id INTEGER,
        PRIMARY KEY (user_id, promo_id)
    )
    """)

    cursor.execute("INSERT OR IGNORE INTO admins (telegram_id, username) VALUES (?, ?)", (ADMIN_ID, ""))

    # ========== ТОВАРЫ ==========
    items_list = [
        # --- MM2 Pets ---
        ("mm2_pet_electro", "mm2", "pets", "Electro", "Питомец Electro из MM2", 15, 1),
        ("mm2_pet_firecat", "mm2", "pets", "Fire Cat", "Питомец Fire Cat из MM2", 15, 2),
        ("mm2_pet_firedog_chroma", "mm2", "pets", "Fire Dog (Chroma)", "Питомец Fire Dog (Chroma) из MM2", 15, 1),
        ("mm2_pet_frostbird", "mm2", "pets", "Frostbird", "Питомец Frostbird из MM2", 15, 1),
        ("mm2_pet_icey", "mm2", "pets", "Icey", "Питомец Icey из MM2", 15, 1),
        ("mm2_pet_phoenix", "mm2", "pets", "Phoenix", "Питомец Phoenix из MM2", 15, 1),
        ("mm2_pet_sammy", "mm2", "pets", "Sammy", "Питомец Sammy из MM2", 15, 1),
        ("mm2_pet_steambird", "mm2", "pets", "Steambird", "Питомец Steambird из MM2", 15, 1),
        ("mm2_pet_traveller", "mm2", "pets", "Traveller", "Питомец Traveller из MM2", 15, 1),
        ("mm2_pet_elitey", "mm2", "pets", "Elitey", "Питомец Elitey из MM2", 15, 2),
        ("mm2_pet_skully", "mm2", "pets", "Skully", "Питомец Skully из MM2", 15, 1),
        # --- MM2 Weapons ---
        ("mm2_weapon_frostbite", "mm2", "weapons", "Frostbite", "Оружие Frostbite из MM2", 10, 1),
        ("mm2_weapon_frostsaber", "mm2", "weapons", "Frostsaber", "Оружие Frostsaber из MM2", 15, 1),
        ("mm2_weapon_swirlyblade", "mm2", "weapons", "Swirly Blade", "Оружие Swirly Blade из MM2", 15, 1),
        # --- Adopt Me Pets ---
        ("adopt_pet_milk_choccybunny", "adoptme", "pets", "Milk Choccybunny", "Питомец Milk Choccybunny (Rare)", 15, 1),
        ("adopt_pet_mochi_meow", "adoptme", "pets", "Mochi Meow", "Питомец Mochi Meow (Legendary)", 30, 3),
        ("adopt_pet_purrowl", "adoptme", "pets", "Purrowl", "Питомец Purrowl (Legendary)", 30, 3),
        ("adopt_pet_shih_tzu", "adoptme", "pets", "Shih Tzu", "Питомец Shih Tzu (Uncommon)", 10, 3),
        ("adopt_pet_japanese_snow_fairy", "adoptme", "pets", "Japanese Snow Fairy", "Питомец Japanese Snow Fairy (Common)", 5, 1),
        ("adopt_pet_stygian_owl_neon", "adoptme", "pets", "Stygian Owl (Neon)", "Питомец Stygian Owl (Neon) (Ultra-Rare)", 20, 1),
        ("adopt_pet_black_footed_ferret_neon", "adoptme", "pets", "Black-Footed Ferret (Neon)", "Питомец Black-Footed Ferret (Neon) (Ultra-Rare)", 20, 1),
        # --- Adopt Me Egg ---
        ("adopt_egg_admin_abuse", "adoptme", "egg", "Admin Abuse Egg", "Яйцо Admin Abuse (Legendary)", 20, 4),
        ("adopt_egg_aztec", "adoptme", "egg", "Aztec Egg", "Яйцо Aztec (Legendary)", 20, 4),
        ("adopt_egg_endangered", "adoptme", "egg", "Endangered Egg", "Яйцо Endangered (Legendary)", 20, 6),
        ("adopt_egg_urban", "adoptme", "egg", "Urban Egg", "Яйцо Urban (Legendary)", 20, 1),
        # --- Adopt Me Boxing ---
        ("adopt_box_rgb_reward", "adoptme", "boxing", "RGB Reward Box", "Коробка RGB Reward", 15, 4),
        ("adopt_box_2d", "adoptme", "boxing", "2D Box", "Коробка 2D", 15, 5),
        ("adopt_box_admin_abuse", "adoptme", "boxing", "Admin Abuse Box", "Коробка Admin Abuse", 15, 4),
        # --- Adopt Me Toys ---
        ("adopt_toy_paint_sealer", "adoptme", "toys", "Paint Sealer", "Игрушка Paint Sealer", 10, 4),
        ("adopt_toy_santa_red_pet_paint", "adoptme", "toys", "Santa Red Pet Paint", "Краска Santa Red Pet Paint", 20, 1),
    ]

    cursor.executemany("""
    INSERT INTO items (code, game, category, name, description, price_stars, stock)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, items_list)

    conn.commit()
    conn.close()

# ================== ОБРАБОТЧИКИ КОМАНД ==================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в PixelShop!\n\n"
        "Используй /help для инструкции, /catalog для просмотра товаров."
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📘 **Инструкция PixelShop**\n\n"
        "**Покупка:**\n"
        "1. Открой /catalog, выбери игру и категорию.\n"
        "2. Нажми на товар — появится окно оплаты звёздами Telegram.\n"
        "3. После оплаты заказ уйдёт администратору, и он свяжется с тобой для выдачи предмета в Roblox.\n\n"
        "**Поиск:** /search <название> — быстрый поиск товара.\n"
        "**Корзина:** /cart — просмотр и оформление выбранных товаров.\n"
        "**Профиль:** /profile — твой ник в Roblox, история заказов, скидки.\n"
        "**Поддержка:** /support — напиши сообщение, администратор ответит.\n"
        "**Промокоды:** /promo <код> — активировать скидку.\n"
        "**Связать ник:** /setnick — указать свой ник в Roblox для быстрой выдачи.\n\n"
        "Бот в бета-версии. Если возникли проблемы — пиши в поддержку."
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("catalog"))
async def cmd_catalog(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Murder Mystery 2", callback_data="game_mm2")],
            [InlineKeyboardButton(text="Adopt Me", callback_data="game_adoptme")],
        ]
    )
    await message.answer("Выберите игру:", reply_markup=keyboard)

@dp.message(Command("search"))
async def cmd_search(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара для поиска:")
    await state.set_state(SearchState.waiting_for_query)

@dp.message(SearchState.waiting_for_query)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.strip()
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, price_stars FROM items WHERE name LIKE ? AND stock > 0",
        (f"%{query}%",)
    )
    items = cursor.fetchall()
    conn.close()

    if not items:
        await message.answer("Ничего не найдено.")
        await state.clear()
        return

    keyboard_builder = []
    for item_id, name, price in items:
        keyboard_builder.append([
            InlineKeyboardButton(text=f"{name} — {price} ⭐", callback_data=f"details_{item_id}")
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_builder)
    await message.answer("Результаты поиска:", reply_markup=keyboard)
    await state.clear()

@dp.message(Command("cart"))
async def cmd_cart(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.name, i.price_stars, c.quantity
        FROM cart c
        JOIN items i ON c.item_id = i.id
        WHERE c.user_id = ?
    """, (user_id,))
    items = cursor.fetchall()
    conn.close()

    if not items:
        await message.answer("Ваша корзина пуста.")
        return

    total = sum(price * qty for _, _, price, qty in items)
    text_lines = ["🛒 **Ваша корзина:**\n"]
    for item_id, name, price, qty in items:
        text_lines.append(f"• {name} — {price}⭐ x{qty} = {price*qty}⭐")
    text_lines.append(f"\n**Итого: {total}⭐**")
    await message.answer("\n".join(text_lines), parse_mode="Markdown")

    keyboard_builder = []
    for item_id, name, price, qty in items:
        keyboard_builder.append([
            InlineKeyboardButton(text=f"Удалить {name}", callback_data=f"remove_from_cart_{item_id}")
        ])
    keyboard_builder.append([
        InlineKeyboardButton(text="Оформить заказ", callback_data="checkout_cart")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_builder)
    await message.answer("Действия:", reply_markup=keyboard)

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT roblox_nick, discount_percent FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    nick = user[0] if user else "не привязан"
    discount = user[1] if user else 0
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status IN ('pending', 'accepted')", (user_id,))
    active_count = cursor.fetchone()[0]
    conn.close()

    await message.answer(
        f"👤 **Профиль**\n\n"
        f"Ник в Roblox: {nick}\n"
        f"Текущая скидка: {discount}%\n"
        f"Завершённых заказов: {completed_count}\n"
        f"Активных заказов: {active_count}\n\n"
        "Привязать/сменить ник: /setnick",
        parse_mode="Markdown"
    )

@dp.message(Command("setnick"))
async def cmd_setnick(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш ник в Roblox:")
    await state.set_state(SetNickState.waiting_for_nick)

@dp.message(SetNickState.waiting_for_nick)
async def process_setnick(message: types.Message, state: FSMContext):
    nick = message.text.strip()
    if not nick:
        await message.answer("Ник не может быть пустым. Попробуйте ещё раз.")
        return
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (telegram_id, roblox_nick) VALUES (?, ?)", (message.from_user.id, nick))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Ник {nick} сохранён!")
    await state.clear()

@dp.message(Command("support"))
async def cmd_support(message: types.Message, state: FSMContext):
    await message.answer("Опишите вашу проблему или вопрос. Мы получим ваше сообщение и скоро ответим.")
    await state.set_state(SupportState.waiting_for_message)

@dp.message(SupportState.waiting_for_message)
async def process_support_message(message: types.Message, state: FSMContext):
    await message.answer("✅ Ваше сообщение получено! Мы рассмотрим его в ближайшее время.")
    admin_text = (
        f"📩 **Новое обращение в поддержку**\n\n"
        f"От: @{message.from_user.username or 'нет username'} (ID {message.from_user.id})\n"
        f"Сообщение:\n{message.text}"
    )
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    await state.clear()

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено. Вы снова можете использовать команды.")

# ================== АДМИНСКАЯ КОМАНДА ОТВЕТА ==================
@dp.message(Command("reply"))
async def cmd_reply(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Недостаточно прав.")
        return
    await message.answer("Введите ID пользователя, которому хотите ответить:")
    await state.set_state(ReplyState.waiting_for_user_id)

@dp.message(ReplyState.waiting_for_user_id)
async def process_reply_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("Некорректный ID. Введите число.")
        return
    await state.update_data(user_id=user_id)
    await message.answer("Введите текст ответа:")
    await state.set_state(ReplyState.waiting_for_reply_text)

@dp.message(ReplyState.waiting_for_reply_text)
async def process_reply_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    if not user_id:
        await message.answer("Ошибка: не найден ID пользователя. Повторите /reply.")
        await state.clear()
        return
    try:
        await bot.send_message(user_id, f"Ответ от поддержки PixelShop:\n\n{message.text}")
        await message.answer("✅ Ответ отправлен.")
    except Exception as e:
        await message.answer(f"Не удалось отправить ответ: {e}")
    await state.clear()

# ================== АДМИНСКИЕ КОМАНДЫ ДЛЯ ТОВАРОВ ==================
@dp.message(Command("additem"))
async def cmd_additem(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="MM2", callback_data="additem_game_mm2")],
            [InlineKeyboardButton(text="Adopt Me", callback_data="additem_game_adoptme")],
        ]
    )
    await message.answer("Выберите игру:", reply_markup=keyboard)
    await state.set_state(AddItemState.waiting_for_game)

@dp.callback_query(F.data.startswith("additem_game_"))
async def additem_game_selected(callback: types.CallbackQuery, state: FSMContext):
    game = callback.data.split("_")[2]
    await state.update_data(game=game)
    await callback.message.edit_text("Введите категорию (pets, weapons, egg, boxing, toys):")
    await state.set_state(AddItemState.waiting_for_category)
    await callback.answer()

@dp.message(AddItemState.waiting_for_category)
async def additem_category_entered(message: types.Message, state: FSMContext):
    category = message.text.strip()
    await state.update_data(category=category)
    await message.answer("Введите название товара:")
    await state.set_state(AddItemState.waiting_for_name)

@dp.message(AddItemState.waiting_for_name)
async def additem_name_entered(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer("Введите описание товара:")
    await state.set_state(AddItemState.waiting_for_description)

@dp.message(AddItemState.waiting_for_description)
async def additem_desc_entered(message: types.Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(desc=desc)
    await message.answer("Введите цену в звёздах (число):")
    await state.set_state(AddItemState.waiting_for_price)

@dp.message(AddItemState.waiting_for_price)
async def additem_price_entered(message: types.Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("Цена должна быть целым числом. Попробуйте ещё раз.")
        return
    await state.update_data(price=price)
    await message.answer("Введите количество (stock):")
    await state.set_state(AddItemState.waiting_for_stock)

@dp.message(AddItemState.waiting_for_stock)
async def additem_stock_entered(message: types.Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
    except ValueError:
        await message.answer("Количество должно быть целым числом. Попробуйте ещё раз.")
        return
    data = await state.get_data()
    game = data.get("game")
    category = data.get("category")
    name = data.get("name")
    desc = data.get("desc")
    price = data.get("price")
    code = f"{game}_{category}_{name.lower().replace(' ', '_')}"

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO items (code, game, category, name, description, price_stars, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, game, category, name, desc, price, stock))
        conn.commit()
        await message.answer(f"Товар **{name}** успешно добавлен!")
    except Exception as e:
        await message.answer(f"Ошибка при добавлении: {e}")
    finally:
        conn.close()
    await state.clear()

@dp.message(Command("removeitem"))
async def cmd_removeitem(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM items")
    items = cursor.fetchall()
    conn.close()

    if not items:
        await message.answer("Нет товаров.")
        return

    keyboard_builder = []
    for item_id, name in items:
        keyboard_builder.append([
            InlineKeyboardButton(text=f"❌ {name}", callback_data=f"removeitem_{item_id}")
        ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_builder)
    await message.answer("Выберите товар для удаления:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("removeitem_"))
async def removeitem_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа.")
        return
    item_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text("Товар удалён.")
    await callback.answer()

@dp.message(Command("edititem"))
async def cmd_edititem(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    await message.answer("Введите ID товара (посмотрите через /listitems):")
    await state.set_state(EditItemState.waiting_for_item_id)

@dp.message(EditItemState.waiting_for_item_id)
async def edititem_id_entered(message: types.Message, state: FSMContext):
    try:
        item_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом.")
        return
    await state.update_data(item_id=item_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Цена", callback_data="editfield_price_stars")],  # ИСПРАВЛЕНО
            [InlineKeyboardButton(text="Количество", callback_data="editfield_stock")],
            [InlineKeyboardButton(text="Название", callback_data="editfield_name")],
            [InlineKeyboardButton(text="Описание", callback_data="editfield_description")],
        ]
    )
    await message.answer("Что вы хотите изменить?", reply_markup=keyboard)
    await state.set_state(EditItemState.waiting_for_field)

@dp.callback_query(F.data.startswith("editfield_"))
async def edititem_field_selected(callback: types.CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]
    await state.update_data(field=field)
    await callback.message.edit_text(f"Введите новое значение для {field}:")
    await state.set_state(EditItemState.waiting_for_value)
    await callback.answer()

@dp.message(EditItemState.waiting_for_value)
async def edititem_value_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    item_id = data.get("item_id")
    field = data.get("field")
    value = message.text.strip()

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    if field in ("price_stars", "stock"):
        try:
            value = int(value)
        except ValueError:
            await message.answer("Значение должно быть числом.")
            conn.close()
            return
        cursor.execute(f"UPDATE items SET {field} = ? WHERE id = ?", (value, item_id))
    else:
        cursor.execute(f"UPDATE items SET {field} = ? WHERE id = ?", (value, item_id))
    conn.commit()
    conn.close()
    await message.answer("✅ Изменения сохранены.")
    await state.clear()

@dp.message(Command("listitems"))
async def cmd_listitems(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_stars, stock FROM items")
    items = cursor.fetchall()
    conn.close()
    if not items:
        await message.answer("Нет товаров.")
        return
    text_lines = ["📋 **Список товаров:**\n"]
    for item_id, name, price, stock in items:
        text_lines.append(f"ID: {item_id} | {name} | {price}⭐ | stock: {stock}")
    await message.answer("\n".join(text_lines), parse_mode="Markdown")

# ================== ПРОМОКОДЫ И СКИДКИ ==================
@dp.message(Command("discounts"))
async def cmd_discounts(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, code, type, value, discount_percent, active FROM promos")
    promos = cursor.fetchall()
    conn.close()
    if not promos:
        await message.answer("Скидок пока нет.")
        return
    text_lines = ["🎁 **Активные скидки:**\n"]
    for promo in promos:
        promo_id, code, p_type, value, discount_percent, active = promo
        if p_type == 'percent':
            desc = f"Процентная скидка: {discount_percent}%"
        else:
            conn = sqlite3.connect("shop.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM items WHERE id = ?", (value,))
            item = cursor.fetchone()
            conn.close()
            item_name = item[0] if item else "Неизвестный товар"
            if discount_percent == 0:
                desc = f"Товар бесплатно: {item_name}"
            else:
                desc = f"Скидка на товар {item_name}: {discount_percent}%"
        status = "✅ активен" if active else "❌ выключен"
        text_lines.append(f"`{code}` — {desc} ({status})")
    await message.answer("\n".join(text_lines), parse_mode="Markdown")

@dp.message(Command("addpromo"))
async def cmd_addpromo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Нет доступа.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Процентная скидка", callback_data="promo_type_percent")],
        [InlineKeyboardButton(text="На конкретный товар", callback_data="promo_type_item")],
    ])
    await message.answer("Выберите тип скидки:", reply_markup=keyboard)
    await state.set_state(AddPromoState.waiting_for_type)

@dp.callback_query(F.data.startswith("promo_type_"))
async def promo_type_selected(callback: types.CallbackQuery, state: FSMContext):
    promo_type = callback.data.split("_")[2]
    await state.update_data(promo_type=promo_type)
    if promo_type == 'percent':
        await callback.message.edit_text("Введите процент скидки (например, 50):")
        await state.set_state(AddPromoState.waiting_for_percent)
    else:
        conn = sqlite3.connect("shop.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM items")
        items = cursor.fetchall()
        conn.close()
        keyboard_builder = []
        for item_id, name in items:
            keyboard_builder.append([
                InlineKeyboardButton(text=f"{name} (ID {item_id})", callback_data=f"promo_item_{item_id}")
            ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_builder)
        await callback.message.edit_text("Выберите товар:", reply_markup=keyboard)
        await state.set_state(AddPromoState.waiting_for_item)
    await callback.answer()

@dp.callback_query(F.data.startswith("promo_item_"))
async def promo_item_selected(callback: types.CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id)
    await callback.message.edit_text("Введите процент скидки на этот товар (0 = бесплатно):")
    await state.set_state(AddPromoState.waiting_for_percent)
    await callback.answer()

@dp.message(AddPromoState.waiting_for_percent)
async def promo_percent_entered(message: types.Message, state: FSMContext):
    try:
        percent = int(message.text.strip())
        if percent < 0 or percent > 100:
            await message.answer("Процент должен быть от 0 до 100.")
            return
    except ValueError:
        await message.answer("Введите целое число.")
        return
    await state.update_data(percent=percent)
    await message.answer("Введите код промокода (например, SALE50):")
    await state.set_state(AddPromoState.waiting_for_code)

@dp.message(AddPromoState.waiting_for_code)
async def promo_code_entered(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = await state.get_data()
    promo_type = data.get("promo_type")
    percent = data.get("percent")
    item_id = data.get("item_id", None)

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    try:
        if promo_type == 'percent':
            cursor.execute("""
                INSERT INTO promos (code, type, value, discount_percent, active)
                VALUES (?, ?, ?, ?, 1)
            """, (code, 'percent', 0, percent))
        else:
            cursor.execute("""
                INSERT INTO promos (code, type, value, discount_percent, active)
                VALUES (?, ?, ?, ?, 1)
            """, (code, 'item', item_id, percent))
        conn.commit()
        await message.answer(f"Промокод `{code}` создан!")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    finally:
        conn.close()
    await state.clear()

@dp.message(Command("promo"))
async def cmd_promo(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Используйте: /promo <код>")
        return
    code = args[1]
    user_id = message.from_user.id
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, value, discount_percent, active FROM promos WHERE code = ?", (code,))
    promo = cursor.fetchone()
    if not promo or promo[4] != 1:
        await message.answer("Промокод не найден или неактивен.")
        conn.close()
        return
    promo_id, p_type, value, discount_percent, active = promo
    if p_type == 'percent':
        cursor.execute("UPDATE users SET discount_percent = ? WHERE telegram_id = ?", (discount_percent, user_id))
        await message.answer(f"Промокод активирован! Скидка {discount_percent}% будет применена к следующему заказу.")
    elif p_type == 'item':
        cursor.execute("SELECT stock FROM items WHERE id = ?", (value,))
        stock = cursor.fetchone()
        if not stock or stock[0] <= 0:
            await message.answer("Товар недоступен.")
            conn.close()
            return
        cursor.execute("INSERT OR REPLACE INTO active_promos (user_id, promo_id) VALUES (?, ?)", (user_id, promo_id))
        await message.answer(f"Промокод на товар активирован! Скидка будет применена при покупке этого товара.")
    conn.commit()
    conn.close()

# ================== CALLBACK-ОБРАБОТЧИКИ КАТАЛОГА ==================
@dp.callback_query(F.data.startswith("game_"))
async def show_categories(callback: types.CallbackQuery):
    game = callback.data.split("_")[1]

    if game == "mm2":
        categories = [
            ("pets", "🐾 Pets"),
            ("weapons", "🔪 Weapons"),
        ]
    elif game == "adoptme":
        categories = [
            ("pets", "🐾 Pets"),
            ("egg", "🥚 Egg"),
            ("boxing", "📦 Box"),
            ("toys", "🧸 Toys"),
        ]
    else:
        await callback.answer("Неизвестная игра", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"cat_{game}_{cat}")]
            for cat, label in categories
        ]
    )
    await callback.message.edit_text("Выберите категорию:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_items(callback: types.CallbackQuery):
    data = callback.data.split("_")
    game = data[1]
    category = data[2]

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, price_stars FROM items WHERE game = ? AND category = ? AND stock > 0",
        (game, category)
    )
    items = cursor.fetchall()
    conn.close()

    if not items:
        await callback.answer("В этой категории пока нет товаров.", show_alert=True)
        return

    keyboard_builder = []
    for item_id, name, price in items:
        keyboard_builder.append([
            InlineKeyboardButton(text=f"{name} — {price}⭐", callback_data=f"details_{item_id}")
        ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_builder)
    category_name = {
        "pets": "Питомцы",
        "weapons": "Оружие",
        "egg": "Яйца",
        "boxing": "📦 Box",
        "toys": "Игрушки",
    }.get(category, "Товары")
    await callback.message.edit_text(f"Товары в категории **{category_name}**:", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("details_"))
async def show_item_details(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, price_stars FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()

    if not item:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    name, description, price = item
    text = f"**{name}**\n{description}\nЦена: {price}⭐"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Купить сейчас", callback_data=f"buy_now_{item_id}")],
            [InlineKeyboardButton(text="В корзину", callback_data=f"add_to_cart_{item_id}")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_now_"))
async def buy_now(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, price_stars FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()

    if not item:
        await callback.answer("Товар не найден!", show_alert=True)
        return

    name, description, price = item

    cursor = conn.cursor()
    cursor.execute("SELECT discount_percent FROM users WHERE telegram_id = ?", (user_id,))
    user_row = cursor.fetchone()
    discount = user_row[0] if user_row else 0
    final_price = int(price * (1 - discount / 100)) if discount > 0 else price

    cursor.execute("""
        SELECT p.discount_percent
        FROM active_promos ap
        JOIN promos p ON ap.promo_id = p.id
        WHERE ap.user_id = ? AND p.type = 'item' AND p.value = ? AND p.active = 1
    """, (user_id, item_id))
    promo_row = cursor.fetchone()
    if promo_row:
        promo_discount = promo_row[0]
        final_price = int(price * (1 - promo_discount / 100))

    if final_price == 0:
        cursor.execute("""
            INSERT INTO orders (user_id, item_id, status, admin_id)
            VALUES (?, ?, 'pending', ?)
        """, (user_id, item_id, ADMIN_ID))
        order_id = cursor.lastrowid
        cursor.execute("UPDATE items SET stock = stock - 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        await callback.message.answer("Ваш заказ бесплатный! Заказ создан и передан администратору.")
        admin_text = f"📦 **Новый заказ #{order_id}**\nТовар: {name}\nЦена: 0 ⭐ (скидка)\nПокупатель: ID {user_id}"
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        return

    prices = [LabeledPrice(label=name, amount=final_price)]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=name,
        description=description,
        payload=f"item_{item_id}",
        currency="XTR",
        provider_token="",
        prices=prices
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM items WHERE id = ?", (item_id,))
    stock = cursor.fetchone()
    if not stock or stock[0] <= 0:
        await callback.answer("Товар недоступен!", show_alert=True)
        conn.close()
        return
    cursor.execute("""
        INSERT INTO cart (user_id, item_id, quantity) VALUES (?, ?, 1)
        ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + 1
    """, (user_id, item_id))
    conn.commit()
    conn.close()
    await callback.answer("Товар добавлен в корзину!", show_alert=True)

@dp.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ? AND item_id = ?", (user_id, item_id))
    conn.commit()
    conn.close()
    await callback.answer("Товар удалён из корзины.")
    await cmd_cart(callback.message)

@dp.callback_query(F.data == "checkout_cart")
async def checkout_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.name, i.price_stars, c.quantity
        FROM cart c
        JOIN items i ON c.item_id = i.id
        WHERE c.user_id = ?
    """, (user_id,))
    items = cursor.fetchall()
    conn.close()

    if not items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT discount_percent FROM users WHERE telegram_id = ?", (user_id,))
    user_row = cursor.fetchone()
    discount = user_row[0] if user_row else 0
    conn.close()

    total = sum(price * qty for _, _, price, qty in items)
    if discount > 0:
        total = int(total * (1 - discount / 100))

    description = "Оформление заказа из корзины"
    prices = [LabeledPrice(label="Общая сумма", amount=total)]
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title="Оформление заказа",
        description=description,
        payload="cart",
        currency="XTR",
        provider_token="",
        prices=prices
    )
    await callback.answer()

# ================== ОПЛАТА ==================
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

def get_admin_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Принять", callback_data=f"accept_{order_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{order_id}")
            ]
        ]
    )

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    if payload.startswith("item_"):
        item_id = int(payload.split("_")[1])
        cursor.execute("""
            INSERT INTO orders (user_id, item_id, status, admin_id)
            VALUES (?, ?, 'pending', ?)
        """, (user_id, item_id, ADMIN_ID))
        order_id = cursor.lastrowid
        cursor.execute("UPDATE items SET stock = stock - 1 WHERE id = ?", (item_id,))
        cursor.execute("SELECT name, price_stars FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        item_name, price = item
        await message.answer("Оплата прошла успешно! Заказ создан и передан администраторам.")
        admin_text = (
            f"📦 **Новый заказ #{order_id}**\n\n"
            f"Товар: {item_name}\n"
            f"Цена: {price} ⭐\n"
            f"Покупатель: ID {user_id} (@{message.from_user.username or 'нет username'})"
        )
        await bot.send_message(ADMIN_ID, admin_text, reply_markup=get_admin_keyboard(order_id), parse_mode="Markdown")

    elif payload == "cart":
        cursor.execute("""
            SELECT i.id, i.name, i.price_stars, c.quantity
            FROM cart c
            JOIN items i ON c.item_id = i.id
            WHERE c.user_id = ?
        """, (user_id,))
        cart_items = cursor.fetchall()
        if not cart_items:
            await message.answer("Корзина пуста, оплата не может быть обработана.")
            conn.commit()
            conn.close()
            return

        order_ids = []
        for item_id, name, price, qty in cart_items:
            for _ in range(qty):
                cursor.execute("""
                    INSERT INTO orders (user_id, item_id, status, admin_id)
                    VALUES (?, ?, 'pending', ?)
                """, (user_id, item_id, ADMIN_ID))
                order_id = cursor.lastrowid
                order_ids.append(order_id)
                cursor.execute("UPDATE items SET stock = stock - 1 WHERE id = ?", (item_id,))

        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await message.answer("Оплата прошла успешно! Заказы созданы и переданны администратору.")
        admin_text = f"📦 **Новые заказы из корзины**\nПокупатель: ID {user_id} (@{message.from_user.username or 'нет username'})\n\n"
        for i, order_id in enumerate(order_ids, 1):
            admin_text += f"Заказ #{order_id}\n"
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

    conn.commit()
    conn.close()

# ================== АДМИНСКИЕ ДЕЙСТВИЯ ==================
@dp.callback_query(F.data.startswith("accept_"))
async def process_accept_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'accepted' WHERE id = ?", (order_id,))
    cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.commit()
    conn.close()

    if order:
        user_id = order[0]
        await bot.send_message(
            user_id,
            "Ваш заказ принят! Добавьте в друзья продавца: https://www.roblox.com/users/4677562267/profile"
        )

    complete_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Завершить", callback_data=f"complete_{order_id}")]
        ]
    )
    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ **Статус: Принят**",
        reply_markup=complete_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer("Заказ принят!")

@dp.callback_query(F.data.startswith("complete_"))
async def process_complete_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,))
    cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.commit()
    conn.close()

    if order:
        user_id = order[0]
        await bot.send_message(user_id, "Заказ выполнен. Спасибо за покупку!")

    await callback.message.edit_text(
        f"{callback.message.text}\n\n🏁 **Статус: Выполнен**",
        parse_mode="Markdown"
    )
    await callback.answer("Заказ завершен!")

@dp.callback_query(F.data.startswith("reject_"))
async def process_reject_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = ?", (order_id,))
    cursor.execute("SELECT item_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    if order:
        item_id = order[0]
        cursor.execute("UPDATE items SET stock = stock + 1 WHERE id = ?", (item_id,))
    cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.commit()
    conn.close()

    if order:
        user_id = order[0]
        await bot.send_message(user_id, "Ваш заказ отклонён. Обратитесь в поддержку.")

    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ **Статус: Отклонён**",
        parse_mode="Markdown"
    )
    await callback.answer("Заказ отклонен!")

# ================== ЗАПУСК ==================
async def main():
    init_db()
    print("Бот PixelShop запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
