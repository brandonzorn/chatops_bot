from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from config import ADMIN_TELEGRAM_IDS
from database import session
from models import Team, RegistrationRequest, Role
from utils import get_admin_keyboard

ASK_NAME, ASK_ROLE, ASK_TEAM, ASK_PHONE = range(4)


async def start_register(update: Update, _):
    await update.message.reply_text("Введите ваше ФИО:")
    return ASK_NAME


async def ask_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text

    roles = session.query(Role).all()
    if not roles:
        await update.message.reply_text(
            "Роли не найдены. Регистрация отменена.",
        )
        return ConversationHandler.END
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
    if not teams:
        await update.message.reply_text(
            "Команды не найдены. Регистрация отменена.",
        )
        return ConversationHandler.END
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


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["team_id"] = int(query.data.split("_")[1])

    keyboard = [
        [
            KeyboardButton(
                "📱 Отправить номер телефона",
                request_contact=True,
            ),
        ],
    ]
    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.callback_query.edit_message_text("Почти готово!")
    await update.effective_user.send_message(
        "Пожалуйста, отправьте ваш номер телефона:",
        reply_markup=markup,
    )
    return ASK_PHONE


async def save_registration(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
):

    team_id = context.user_data["team_id"]
    full_name = context.user_data["full_name"]
    role_id = context.user_data["role_id"]
    telegram_id = update.effective_user.id
    telegram_username = update.effective_user.username
    phone_number = update.message.contact.phone_number

    existing = session.query(
        RegistrationRequest,
    ).filter_by(
        id=telegram_id,
    ).first()
    if existing:
        await update.message.reply_text(
            "Вы уже подали заявку.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    request = RegistrationRequest(
        id=telegram_id,
        full_name=full_name,
        telegram_username=telegram_username,
        phone_number=phone_number,
        role_id=role_id,
        team_id=team_id,
    )
    session.add(request)
    session.commit()

    reply_markup = ReplyKeyboardRemove()
    if str(telegram_id) in ADMIN_TELEGRAM_IDS:
        reply_markup = get_admin_keyboard()

    await update.message.reply_text(
        "Заявка на регистрацию отправлена. Ожидайте подтверждения.",
        reply_markup=reply_markup,
    )
    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END


registration_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler("start", start_register),
        CommandHandler("register", start_register),
    ],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_role)],
        ASK_ROLE: [CallbackQueryHandler(ask_team, pattern="^role_")],
        ASK_TEAM: [CallbackQueryHandler(ask_phone, pattern="^team_")],
        ASK_PHONE: [MessageHandler(filters.CONTACT, save_registration)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "registration_conv",
]
