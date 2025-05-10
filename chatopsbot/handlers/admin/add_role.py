from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from models import Role
from database import session
from utils import require_admin


@require_admin
async def add_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ Использование: /add_role <название роли>",
        )
        return
    role_name = " ".join(context.args).strip()
    if session.query(Role).filter_by(role_name=role_name).first():
        await update.message.reply_text("❌ Такая роль уже существует.")
        return
    new_role = Role(
        role_name=role_name,
    )
    session.add(new_role)
    session.commit()
    await update.message.reply_text(f"✅ Роль '{role_name}' добавлена.")


add_role_handler = CommandHandler("add_role", add_role_command)


__all__ = [
    "add_role_handler",
]
