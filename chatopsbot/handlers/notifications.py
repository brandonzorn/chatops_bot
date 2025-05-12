from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import session
from models import Service, ServiceSubscription, Employee
from utils import require_registration

CHOOSE_SERVICE = 3


@require_registration
async def start_subscribe(update: Update, _):
    user_id = update.effective_user.id

    employee = session.query(Employee).filter_by(id=user_id).first()
    if not employee:
        await update.message.reply_text("Вы не зарегистрированы.")
        return ConversationHandler.END
    services = session.query(Service).filter_by(team_id=employee.team_id).all()
    if not services:
        await update.message.reply_text("Нет доступных сервисов.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                service.name,
                callback_data=f"subscribe_{service.id}",
            ),
        ]
        for service in services
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите сервис для подписки:",
        reply_markup=reply_markup,
    )
    return CHOOSE_SERVICE


async def handle_service_choice(update: Update, _):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("subscribe_"):
        await query.edit_message_text("Некорректный выбор.")
        return ConversationHandler.END

    service_id = int(data.split("_")[1])
    user_id = update.effective_user.id

    employee = session.query(Employee).filter_by(id=user_id).first()

    if not employee:
        await query.edit_message_text("Вы не зарегистрированы.")
        return ConversationHandler.END

    exists = session.query(ServiceSubscription).filter_by(
        employee_id=employee.id,
        service_id=service_id,
    ).first()

    service = session.get(Service, service_id)
    if exists:
        session.delete(exists)
        await query.edit_message_text(f"Подписка на {service.name} отменена.")
    else:
        session.add(
            ServiceSubscription(
                employee_id=employee.id,
                service_id=service_id,
            ),
        )
        await query.edit_message_text(f"Подписка на {service.name} оформлена.")
    session.commit()
    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Подписка отменена.")
    return ConversationHandler.END


subscribe_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("gitlab_subscribe", start_subscribe)],
    states={
        CHOOSE_SERVICE: [
            CallbackQueryHandler(handle_service_choice, pattern="^subscribe_"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


@require_registration
async def silence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Пожалуйста, укажите количество часов для остановки уведомлений.",
        )
        return
    subscriptions = session.query(
        ServiceSubscription,
    ).filter_by(
        employee_id=update.effective_user.id,
    ).all()
    if not subscriptions:
        await update.message.reply_text(
            "Вы не подписаны на уведомления.",
        )
        return
    for subscription in subscriptions:
        subscription.set_subscription_end(hours)
    session.commit()
    await update.message.reply_text(
        f"Уведомления приостановлены на {hours} часов.",
    )

silence_handler = CommandHandler("silence", silence)

__all__ = [
    "subscribe_conv",
    "silence_handler",
]
