from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from models import Role
from database import session
from utils import require_admin


ASK_ROLE_NAME = 0


@require_admin
async def start_add_role(update: Update, _) -> int:
    await update.message.reply_text("Введите название роли:")
    return ASK_ROLE_NAME


async def save_role(update: Update, _):
    role_name = update.message.text.strip()
    if session.query(Role).filter_by(role_name=role_name).first():
        await update.message.reply_text("❌ Такая роль уже существует.")
        return ConversationHandler.END
    new_role = Role(
        role_name=role_name,
    )
    session.add(new_role)
    session.commit()
    await update.message.reply_text(f"✅ Роль '{role_name}' добавлена.")
    return ConversationHandler.END


async def cancel(update: Update, _) -> int:
    await update.message.reply_text("🚫 Добавление роли отменено.")
    return ConversationHandler.END


add_role_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[
        CommandHandler("add_role", start_add_role),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^Добавить роль$"),
            start_add_role,
        ),
    ],
    states={
        ASK_ROLE_NAME: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                save_role,
            ),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "add_role_conv",
]
