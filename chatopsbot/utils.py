from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_TELEGRAM_ID
from database import session
from models import Employee


def require_registration(func):
    @wraps(func)
    async def wrapper(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args,
            **kwargs,
    ):
        employee = session.query(
            Employee,
        ).filter_by(
            id=update.effective_user.id,
        ).first()
        if employee is None:
            await update.message.reply_text(
                "Вы не зарегистрированы или ваша заявка ещё не одобрена. "
                "Пожалуйста, начните с команды /registration.",
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_admin(func):
    @wraps(func)
    async def wrapper(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            *args,
            **kwargs,
    ):
        if update.effective_user.id != ADMIN_TELEGRAM_ID:
            await update.message.reply_text(
                "⛔ У вас нет доступа к этой команде.",
            )
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper


async def send_invite_links(employee, context: ContextTypes.DEFAULT_TYPE):
    chat_ids = [
        employee.team.chat_id,
        employee.role.chat_id,
    ]

    links = []
    for chat_id in chat_ids:
        if not chat_id:
            continue
        link = await context.bot.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=1,
            expire_date=None,
            creates_join_request=False,
        )
        links.append(link.invite_link)

    await context.bot.send_message(
        chat_id=employee.id,
        text=f"Добро пожаловать! "
             f"Вот ссылки на чаты вашей команды: {'\n'.join(links)}",
    )


__all__ = [
    "require_admin",
    "require_registration",
    "send_invite_links",
]
