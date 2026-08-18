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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        game TEXT,
        name TEXT,
        description TEXT,
        price_stars INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        admin_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT
    )
    """)

    cursor.execute("INSERT OR IGNORE INTO admins (telegram_id, username) VALUES (?, ?)", (ADMIN_ID, ""))

    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        items_list = [
            ("mm2_pet_electro", "mm2", "Electro", "Питомец Electro из MM2", 15),
            ("mm2_pet_firecat", "mm2", "Fire Cat", "Питомец Fire Cat из MM2", 15),
            ("mm2_pet_firedog_chroma", "mm2", "Fire Dog (Chroma)", "Питомец Fire Dog (Chroma) из MM2", 15),
            ("mm2_pet_frostbird", "mm2", "Frostbird", "Питомец Frostbird из MM2", 15),
            ("mm2_pet_icey", "mm2", "Icey", "Питомец Icey из MM2", 15),
            ("mm2_pet_phoenix", "mm2", "Phoenix", "Питомец Phoenix из MM2", 15),
            ("mm2_pet_sammy", "mm2", "Sammy", "Питомец Sammy из MM2", 15),
            ("mm2_pet_steambird", "mm2", "Steambird", "Питомец Steambird из MM2", 15),
            ("mm2_pet_traveller", "mm2", "Traveller", "Питомец Traveller из MM2", 15),
            ("mm2_pet_elitey", "mm2", "Elitey", "Питомец Elitey из MM2", 15),
            ("mm2_pet_skully", "mm2", "Skully", "Питомец Skully из MM2", 15),
            ("mm2_weapon_frostbite", "mm2", "Frostbite", "Оружие Frostbite из MM2", 10),
            ("mm2_weapon_frostsaber", "mm2", "Frostsaber", "Оружие Frostsaber из MM2", 15),
            ("mm2_weapon_swirlyblade", "mm2", "Swirly Blade", "Оружие Swirly Blade из MM2", 15)
        ]
        cursor.executemany("""
        INSERT INTO items (code, game, name, description, price_stars)
        VALUES (?, ?, ?, ?, ?)
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
            [types.InlineKeyboardButton(text="Murder Mystery 2", callback_data="cat_mm2")]
        ]
    )
    await message.answer("Выберите категорию игр:", reply_markup=keyboard)

@dp.callback_query(F.data == "cat_mm2")
async def show_mm2_items(callback: types.CallbackQuery):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_stars FROM items WHERE game = 'mm2'")
    items = cursor.fetchall()
    conn.close()

    keyboard_builder = []
    for item_id, name, price in items:
        keyboard_builder.append([
            types.InlineKeyboardButton(
                text=f"{name} — {price} ⭐",
                callback_data=f"buy_{item_id}"
            )
        ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_builder)
    await callback.message.edit_text("Товары в категории **Murder Mystery 2**:", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

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

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

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
