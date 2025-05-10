from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from models import Team
from database import session
from utils import require_admin

ASK_TEAM_NAME, ASK_TEAM_DESCRIPTION = range(2)


@require_admin
async def start_add_team(update: Update, _) -> int:
    await update.message.reply_text("Введите имя команды:")
    return ASK_TEAM_NAME


async def save_team_name(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int:
    name = update.message.text.strip()
    if session.query(Team).filter_by(name=name).first():
        await update.message.reply_text(
            "❌ Команда с таким именем уже существует.",
        )
        return ConversationHandler.END

    context.user_data["team_name"] = name
    await update.message.reply_text("Введите описание команды:")
    return ASK_TEAM_DESCRIPTION


async def save_team_description(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
) -> int:
    description = update.message.text.strip()
    name = context.user_data["team_name"]

    new_team = Team(
        name=name,
        description=description,
    )
    session.add(new_team)
    session.commit()

    await update.message.reply_text(f"✅ Команда '{name}' добавлена.")
    return ConversationHandler.END


async def cancel(update: Update, _) -> int:
    await update.message.reply_text("🚫 Добавление команды отменено.")
    return ConversationHandler.END


add_team_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("add_team", start_add_team)],
    states={
        ASK_TEAM_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_team_name,
            ),
        ],
        ASK_TEAM_DESCRIPTION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_team_description,
            ),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "add_team_conv",
]
