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

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

TOKEN = "8804500426:AAH99VEUOYVyf3CS277Kp9ZdwOdFniBtyrQ"  # <-- ЗАМЕНИ НА СВОЙ ТОКЕН
ADMIN_ID = 2087257865

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    # Удаляем старые таблицы (заказы будут сброшены)
    cursor.execute("DROP TABLE IF EXISTS items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS admins")

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

    cursor.execute("INSERT OR IGNORE INTO admins (telegram_id, username) VALUES (?, ?)", (ADMIN_ID, ""))

    # ========== ТОВАРЫ ==========
    # Структура: (code, game, category, name, description, price_stars, stock)
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в PixelShop! Напиши /catalog, чтобы посмотреть товары.")

@dp.message(Command("catalog"))
async def cmd_catalog(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Murder Mystery 2", callback_data="game_mm2")],
            [types.InlineKeyboardButton(text="Adopt Me", callback_data="game_adoptme")],
        ]
    )
    await message.answer("Выберите игру:", reply_markup=keyboard)

# Обработка выбора игры
@dp.callback_query(F.data.startswith("game_"))
async def show_categories(callback: types.CallbackQuery):
    game = callback.data.split("_")[1]  # mm2 или adoptme

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

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=label, callback_data=f"cat_{game}_{cat}")]
            for cat, label in categories
        ]
    )

    await callback.message.edit_text("Выберите категорию:", reply_markup=keyboard)
    await callback.answer()

# Обработка выбора категории (подкатегории)
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
            types.InlineKeyboardButton(
                text=f"{name} — {price} ⭐",
                callback_data=f"buy_{item_id}"
            )
        ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_builder)

    category_name = {
        "pets": "Питомцы",
        "weapons": "Оружие",
        "egg": "Яйца",
        category_name = {
        "pets": "Питомцы",
        "weapons": "Оружие",
        "egg": "Яйца",
        "boxing": "коробки",
        "toys": "Игрушки",
    }.get(category, "Товары")

    await callback.message.edit_text(f"Товары в категории **{category_name}**:", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Покупка товара
        "toys": "Игрушки",
    }.get(category, "Товары")

    await callback.message.edit_text(f"Товары в категории **{category_name}**:", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Покупка товара
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
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

    prices = [LabeledPrice(label=name, amount=price)]

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

# Проверка перед оплатой
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Успешная оплата
@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    item_id = int(payload.split("_")[1])
    user_id = message.from_user.id

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO orders (user_id, item_id, status, admin_id)
    VALUES (?, ?, 'pending', ?)
    """, (user_id, item_id, ADMIN_ID))
    order_id = cursor.lastrowid

    # Уменьшаем количество товара
    cursor.execute("UPDATE items SET stock = stock - 1 WHERE id = ?", (item_id,))

    cursor.execute("SELECT name, price_stars FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.commit()
    conn.close()

    item_name, price = item

    await message.answer("Оплата прошла успешно! Заказ создан и передан администраторам.")

    admin_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Принять", callback_data=f"accept_{order_id}"),
                types.InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{order_id}")
            ]
        ]
    )

    admin_text = (
        f"📦 **Новый заказ #{order_id}**\n\n"
        f"Товар: {item_name}\n"
        f"Цена: {price} ⭐\n"
        f"Покупатель: ID {user_id} (@{message.from_user.username or 'нет username'})"
    )

    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_keyboard, parse_mode="Markdown")

# Принять заказ
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

    complete_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Завершить", callback_data=f"complete_{order_id}")]
        ]
    )

    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ **Статус: Принят**",
        reply_markup=complete_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer("Заказ принят!")

# Завершить заказ
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

# Отклонить заказ
@dp.callback_query(F.data.startswith("reject_"))
async def process_reject_order(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])

    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = ?", (order_id,))
    # Возвращаем товар в магазин
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

async def main():
    init_db()
    print("Бот PixelShop запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
