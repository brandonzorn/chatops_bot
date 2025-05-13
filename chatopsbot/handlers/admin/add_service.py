from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from models import Service, Team
from database import session
from utils import require_admin


ASK_SERVICE_NAME, ASK_REPO_NAME, ASK_TEAM = range(3)


@require_admin
async def start_add_service(update: Update, _) -> int:
    await update.message.reply_text("Введите название сервиса:")
    return ASK_SERVICE_NAME


async def save_service_name(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int:
    context.user_data["service_name"] = update.message.text.strip()
    await update.message.reply_text("Введите имя репозитория (GitLab):")
    return ASK_REPO_NAME


async def save_repo_name(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int:
    repo_name = update.message.text.strip()

    if session.query(Service).filter_by(git_repo_name=repo_name).first():
        await update.message.reply_text(
            "❌ Такой репозиторий уже зарегистрирован.",
        )
        return ConversationHandler.END

    context.user_data["repo_name"] = repo_name

    teams = session.query(Team).all()
    if not teams:
        await update.message.reply_text("❗ Нет доступных команд.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                team.name,
                callback_data=f"addServiceTeam_{team.id}",
            ),
        ]
        for team in teams
    ]
    await update.message.reply_text(
        "Выберите команду для сервиса:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ASK_TEAM


async def save_team(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    team_id = int(query.data.split("_")[1])

    new_service = Service(
        name=context.user_data["service_name"],
        git_repo_name=context.user_data["repo_name"],
        team_id=team_id,
    )
    session.add(new_service)
    session.commit()

    await query.edit_message_text(f"✅ Сервис '{new_service.name}' добавлен.")
    return ConversationHandler.END


async def cancel(update: Update, _) -> int:
    await update.message.reply_text("🚫 Добавление сервиса отменено.")
    return ConversationHandler.END


add_service_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler("add_service", start_add_service),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Добавить сервис$"),
            start_add_service,
        ),
    ],
    states={
        ASK_SERVICE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_service_name),
        ],
        ASK_REPO_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_repo_name),
        ],
        ASK_TEAM: [
            CallbackQueryHandler(save_team, pattern="^addServiceTeam_"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "add_service_conv",
]
