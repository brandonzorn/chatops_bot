from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from database import session
from models import Service
from utils import require_admin

CHOOSE_SERVICE, ENTER_THRESHOLD = range(2)


@require_admin
async def start_set_threshold(update: Update, _):
    services = session.query(Service).all()
    if not services:
        await update.message.reply_text("Нет сервисов для настройки.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                service.name,
                callback_data=f"service_{service.id}",
            ),
        ]
        for service in services
    ]
    await update.message.reply_text(
        "Выберите сервис для настройки порога уведомлений:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_SERVICE


async def ask_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    service_id = int(query.data.split("_")[1])
    context.user_data["service_id"] = service_id

    service = session.get(Service, service_id)
    await query.edit_message_text(
        f"Введите новый порог уведомления (0 до 100)"
        f" для сервиса {service.name}:",
    )
    return ENTER_THRESHOLD


async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(update.message.text)
        if not (0 <= value <= 100):
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Введите корректное число от 0 до 100.",
        )
        return ENTER_THRESHOLD

    service_id = context.user_data["service_id"]
    service = session.get(Service, service_id)
    service.notification_threshold = value
    session.commit()

    await update.message.reply_text(
        f"✅ Порог уведомления для {service.name} установлен на {value}%.",
    )
    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


threshold_conv = ConversationHandler(
    entry_points=[CommandHandler("change_threshold", start_set_threshold)],
    states={
        CHOOSE_SERVICE: [
            CallbackQueryHandler(
                ask_threshold,
                pattern="^service_",
            ),
        ],
        ENTER_THRESHOLD: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                set_threshold,
            ),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "threshold_conv",
]
