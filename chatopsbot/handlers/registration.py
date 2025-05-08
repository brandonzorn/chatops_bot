from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from database import session
from models import Team, RegistrationRequest, Role

ASK_NAME, ASK_ROLE, ASK_TEAM = range(3)


async def start_register(update: Update, _):
    await update.message.reply_text("Введите ваше ФИО:")
    return ASK_NAME


async def ask_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text

    roles = session.query(Role).all()
    keyboard = [
        [InlineKeyboardButton(role.role_name, callback_data=f"role_{role.id}")]
        for role in roles
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите вашу роль:",
        reply_markup=markup,
    )
    return ASK_ROLE


async def ask_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["role_id"] = query.data.split("_")[1]

    teams = session.query(Team).all()
    keyboard = [
        [InlineKeyboardButton(team.name, callback_data=f"team_{team.id}")]
        for team in teams
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Выберите вашу команду:",
        reply_markup=markup,
    )
    return ASK_TEAM


async def save_registration(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    team_id = int(query.data.split("_")[1])
    full_name = context.user_data["full_name"]
    role_id = context.user_data["role_id"]
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username

    existing = session.query(
        RegistrationRequest,
    ).filter_by(
        id=telegram_id,
    ).first()
    if existing:
        await update.callback_query.edit_message_text("Вы уже подали заявку.")
        return ConversationHandler.END

    request = RegistrationRequest(
        id=telegram_id,
        full_name=full_name,
        telegram_username=telegram_username,
        role_id=role_id,
        team_id=team_id,
    )
    session.add(request)
    session.commit()

    await update.callback_query.edit_message_text(
        "Заявка на регистрацию отправлена. Ожидайте подтверждения.",
    )
    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END


registration_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("register", start_register)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_role)],
        ASK_ROLE: [CallbackQueryHandler(ask_team, pattern="^role_")],
        ASK_TEAM: [CallbackQueryHandler(save_registration, pattern="^team_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "registration_conv",
]
