from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
from models import RegistrationRequest, Employee
from utils import require_admin, send_invite_links

CHOOSE_REQUEST, HANDLE_ACTION = range(2)


@require_admin
async def start_review(update: Update, _):
    requests = session.query(RegistrationRequest).all()
    if not requests:
        await update.message.reply_text("Нет заявок на рассмотрение.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                f"{req.full_name} ({req.role.role_name})",
                callback_data=f"view_{req.id}",
            ),
        ]
        for req in requests
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите заявку для просмотра:",
        reply_markup=markup,
    )
    return CHOOSE_REQUEST


async def view_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    req_id = int(query.data.split("_")[1])
    request = session.get(RegistrationRequest, req_id)
    if not request:
        await query.edit_message_text("Заявка не найдена.")
        return ConversationHandler.END

    context.user_data["selected_request_id"] = req_id

    text = (
        f"📄 Заявка\n"
        f"👤 ФИО: {request.full_name}\n"
        f"🧑‍💻 Роль: {request.role.role_name}\n"
        f"👥 Команда: {request.team.name}\n\n"
        f"Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Принять", callback_data="approve"),
            InlineKeyboardButton("❌ Отклонить", callback_data="reject"),
        ],
    ])
    await query.edit_message_text(text, reply_markup=keyboard)
    return HANDLE_ACTION


async def handle_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data
    req_id = context.user_data.get("selected_request_id")
    request = session.get(RegistrationRequest, req_id)

    if not request:
        await query.edit_message_text("Заявка не найдена или уже обработана.")
        return ConversationHandler.END

    if action == "approve":
        employee = session.query(Employee).filter_by(id=request.id).first()
        if employee:
            employee.full_name = request.full_name
            employee.telegram_username = request.telegram_username
            employee.phone_number = request.phone_number
            employee.role_id = request.role_id
            employee.team_id = request.team_id
        else:
            employee = Employee(
                id=request.id,
                full_name=request.full_name,
                telegram_username=request.telegram_username,
                phone_number=request.phone_number,
                role_id=request.role_id,
                team_id=request.team_id,
            )
            session.add(employee)
        session.delete(request)
        session.commit()

        await send_invite_links(employee, context)

        await query.edit_message_text(
            f"✅ Заявка от {employee.full_name} одобрена.",
        )
    else:
        session.delete(request)
        session.commit()
        await query.edit_message_text(
            f"❌ Заявка от {request.full_name} отклонена.",
        )

    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Рассмотрение заявок отменено.")
    return ConversationHandler.END


review_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler("review_requests", start_review),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Просмотр заявок$"),
            start_review,
        ),
    ],
    states={
        CHOOSE_REQUEST: [
            CallbackQueryHandler(view_request, pattern="^view_"),
        ],
        HANDLE_ACTION: [
            CallbackQueryHandler(
                handle_decision,
                pattern="^(approve|reject)$",
            ),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "review_conv",
]
