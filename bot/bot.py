from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes,
    CommandHandler, CallbackQueryHandler
)
import os
import httpx
from postgres import SessionLocal, get_products_info

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROCESSOR_URL = os.getenv("PROCESSOR_URL")

# Хранилище корзин: user_id -> {prod_id: (name, price)}
user_carts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, который поможет составить заказ 😋\n🧐 Узнай подробности о конкретном продукте\n📝 Попроси составить заказ\n\n📌 Старайся более точно описать то, что хочешь")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    context.user_data["last_query"] = text  # Сохраняем последний запрос пользователя

    failed = False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PROCESSOR_URL}/process",
                json={"text": text, "user_id": str(user_id)}
            )
    except Exception:
        failed = True

    if failed or response.status_code != 200:
        await update.message.reply_text("⚠️ Ошибка обработки сообщения")
        return

    response_json = response.json()

    if not response_json['outputs']:
        await update.message.reply_text('Вариантов не найдено :(')
        return

    if response_json['action'] == 0:
        # Просто выводим информацию
        for ent in response_json['outputs']:
            products = get_products_info(SessionLocal(), response_json['outputs'][ent])
            await update.message.reply_text('Информация про ' + ent)
            for _, name, info, price in products:
                await update.message.reply_text(f'{name}:\n\n{info}\n\n   * {price} ₽')

    elif response_json['action'] == 1:
        # Для каждого ent с вариантами формируем кнопки
        for ent in response_json['outputs']:
            products = get_products_info(SessionLocal(), response_json['outputs'][ent])
            keyboard = []
            for prod_id, name, info, price in products:
                callback_data = f"addcart|{prod_id}"
                keyboard.append([InlineKeyboardButton(f"{name} - {price} ₽", callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f'Найдены следующие продукты для "{ent}":', reply_markup=reply_markup)

        # Кнопка для показа корзины
        show_cart_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Показать корзину 🛒", callback_data="showcart")]]
        )
        await update.message.reply_text("Когда выберете все продукты, нажмите кнопку ниже:", reply_markup=show_cart_button)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    data = query.data.split("|")
    action = data[0]

    if action == "addcart":
        prod_id = data[1]
        # Загрузка данных о продукте из БД по prod_id
        with SessionLocal() as session:
            products = get_products_info(session, [prod_id])
            if not products:
                await query.edit_message_text("⚠️ Продукт не найден.")
                return
            # products возвращает список кортежей, берем первый
            _, name, _, price = products[0]

        cart = user_carts.setdefault(user_id, {})
        cart[prod_id] = (name, price)
        await query.edit_message_text(f"Добавлено в корзину: {name} - {price} ₽")

    elif action == "showcart":
        cart = user_carts.get(user_id, {})
        if not cart:
            await query.edit_message_text("Ваша корзина пуста.")
            return
        text_lines = ["Ваша корзина:\n"]
        total = 0
        for name, price in cart.values():
            text_lines.append(f"{name} — {price} ₽")
            total += price
        text_lines.append(f"\nИтого: {total} ₽")

        keyboard = [
            [InlineKeyboardButton("Пересобрать заказ 🔄", callback_data="rebuildcart")],
            [InlineKeyboardButton("Всё супер! ✅", callback_data="confirmcart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("\n".join(text_lines), reply_markup=reply_markup)

    elif action == "rebuildcart":
        last_query = context.user_data.get("last_query")
        if not last_query:
            await query.edit_message_text("Нет предыдущего запроса для пересборки.")
            return

        # Очистка корзины перед пересборкой
        user_carts[user_id] = {}

        # Создаём фейковый update с тем же текстом для повторного вызова handle_message
        class FakeMessage:
            def __init__(self, text, user):
                self.text = text
                self.from_user = user
                self.chat = user

            async def reply_text(self, *args, **kwargs):
                pass

        class FakeUpdate:
            def __init__(self, message):
                self.message = message
                self.effective_user = message.from_user
                self.effective_chat = message.chat

        fake_message = FakeMessage(last_query, update.effective_user)
        fake_update = FakeUpdate(fake_message)

        await handle_message(fake_update, context)

    elif action == "confirmcart":
        user_carts[user_id] = {}
        await query.edit_message_text("Спасибо! Ваш заказ принят ✅")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()
