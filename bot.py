from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем настройки из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

if not BOT_TOKEN or not ADMIN_ID:
    logger.error("❌ BOT_TOKEN или ADMIN_ID не установлены!")
    exit(1)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

Это бот для связи с владельцем. 
Просто напиши свое сообщение, и я перешлю его.
"""
    
    keyboard = [
        [KeyboardButton("📝 Написать сообщение")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    # Уведомляем владельца (только ему показываем данные)
    admin_text = f"""
🆕 Новый пользователь:
├ ID: `{user.id}`
├ Имя: {user.first_name or 'Не указано'}
├ Фамилия: {user.last_name or 'Не указана'}
└ Юзернейм: @{user.username or 'Не указан'}
"""
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')
        logger.info(f"✅ Уведомление отправлено владельцу")
    except Exception as e:
        logger.error(f"❌ Ошибка уведомления владельцу: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
ℹ️ Помощь по боту:

• Напиши любое сообщение - я перешлю его владельцу
• Владелец ответит тебе когда сможет
• Ответ придет тебе в этот чат

Всё просто! ✨
"""
    await update.message.reply_text(help_text)

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text
    
    # Игнорируем кнопки
    if user_message in ["📝 Написать сообщение", "ℹ️ Помощь"]:
        if user_message == "ℹ️ Помощь":
            await help_command(update, context)
        else:
            await update.message.reply_text("Напиши свое сообщение и я перешлю его владельцу! ✉️")
        return
    
    # Сообщение для владельца (с данными пользователя)
    admin_message = f"""
📩 Новое сообщение от пользователя:

👤 Информация об отправителе:
├ ID: `{user.id}`
├ Имя: {user.first_name or 'Не указано'}
├ Фамилия: {user.last_name or 'Не указана'}
└ Юзернейм: @{user.username or 'Не указан'}

📝 Сообщение:
{user_message}
"""
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='Markdown')
        await update.message.reply_text("✅ Сообщение отправлено владельцу! Ожидай ответа.")
        logger.info(f"✅ Сообщение от {user.id} отправлено владельцу")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        await update.message.reply_text("❌ Ошибка отправки. Попробуй позже.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответь на сообщение пользователя!")
        return
    
    reply_to_message = update.message.reply_to_message.text
    admin_reply = update.message.text
    
    try:
        if "ID: `" in reply_to_message:
            user_id_start = reply_to_message.find("ID: `") + 5
            user_id_end = reply_to_message.find("`", user_id_start)
            user_id = int(reply_to_message[user_id_start:user_id_end])
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📨 Ответ от владельца:\n\n{admin_reply}"
                )
                await update.message.reply_text("✅ Ответ отправлен пользователю!")
            except Exception as e:
                if "bot was blocked" in str(e).lower():
                    await update.message.reply_text("❌ Пользователь заблокировал бота.")
                else:
                    await update.message.reply_text(f"❌ Ошибка отправки: {e}")
    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")
        await update.message.reply_text("❌ Ошибка обработки ответа.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(📝 Написать сообщение|ℹ️ Помощь)$"), 
        handle_user_message
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, 
        handle_user_message
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Chat(ADMIN_ID), 
        handle_admin_reply
    ))
    
    # Запуск бота
    print("🚀 Бот запущен на Render!")
    print(f"📍 Владелец ID: {ADMIN_ID}")
    application.run_polling()

if __name__ == '__main__':
    main()
