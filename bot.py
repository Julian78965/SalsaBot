import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from parser import parse_input, format_confirmation, detect_command
from google_calendar import create_event, delete_event, find_events
from notion_db import create_notion_entry, delete_notion_entry, find_notion_entries

load_dotenv()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

AUTHORIZED_USER = os.getenv('AUTHORIZED_USER_ID')

def is_authorized(update):
    if not AUTHORIZED_USER:
        return True
    return str(update.effective_user.id) == str(AUTHORIZED_USER)

async def start(update, context):
    if not is_authorized(update):
        return
    welcome = (
        "🌶️ *SalsaBot activo!*\n\n"
        "*Crear:*\n"
        "• `Feria Eva 7 mayo 7:30AM prioridad 1`\n\n"
        "*Borrar:*\n"
        "• `borrar Feria Eva`\n\n"
        "*Editar:*\n"
        "• `editar Feria Eva hora a 9AM`\n\n"
        "Tu ID: `" + str(update.effective_user.id) + "`"
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def handle_message(update, context):
    if not is_authorized(update):
        return
    text = update.message.text
    if not text:
        return
    processing_msg = await update.message.reply_text("⏳ Procesando...")
    try:
        command = detect_command(text)
        if command and command['command'] == 'delete':
            title = command['title']
            events = find_events(title)
            if not events:
                await processing_msg.edit_text(f"❌ No encontré ningún evento llamado *{title}*", parse_mode='Markdown')
                return
            event = events[0]
            keyboard = [[
                InlineKeyboardButton("✅ Sí, borrar", callback_data=f"del_{event['id']}|{title}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel")
            ]]
            await processing_msg.edit_text(
                f"¿Borrar *{event['summary']}*?",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            parsed = parse_input(text)
            results = []
            cal_success, cal_result = create_event(parsed)
            results.append("📅 Google Calendar ✅" if cal_success else f"📅 Calendar ❌ ({cal_result})")
            notion_success, notion_result = create_notion_entry(parsed)
            results.append("📋 Notion ✅" if notion_success else f"📋 Notion ❌ ({notion_result})")
            confirmation = format_confirmation(parsed)
            await processing_msg.edit_text(f"{confirmation}\n\nEstado:\n{chr(10).join(results)}")
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("❌ Cancelado.")
        return
    if data.startswith("del_"):
        parts = data[4:].split("|", 1)
        event_id = parts[0]
        event_name = parts[1] if len(parts) > 1 else "evento"
        cal_success, cal_msg = delete_event(event_id)
        notion_success, notion_msg = delete_notion_entry(event_name)
        results = []
        results.append("📅 Google Calendar ✅" if cal_success else f"📅 Calendar ❌")
        results.append("📋 Notion ✅" if notion_success else f"📋 Notion ❌")
        await query.edit_message_text(f"🗑 *{event_name}* borrado\n\n" + '\n'.join(results), parse_mode='Markdown')

async def help_command(update, context):
    help_text = (
        "🌶️ *SalsaBot — Comandos*\n\n"
        "*Crear:* `Feria Eva 7 mayo 7:30AM prioridad 1`\n"
        "*Borrar:* `borrar Feria Eva`\n"
        "*Editar:* `editar Feria Eva hora a 9AM`\n\n"
        "*Prioridades:*\n"
        "🔴 prioridad 1 / alta\n"
        "🟡 prioridad 2 / media\n"
        "🟢 prioridad 3 / baja"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_TOKEN no configurado")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🌶️ SalsaBot iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
