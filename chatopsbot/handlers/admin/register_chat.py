from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

from database import session
from models import Role, Team
from utils import require_admin

CHOOSE_TYPE, CHOOSE_ROLE, CHOOSE_TEAM = range(3)


@require_admin
async def start_register(update: Update, _):
    chat = update.effective_chat

    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text(
            "Эту команду нужно использовать в группе.",
        )
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Роль", callback_data="assignRole"),
            InlineKeyboardButton("Команда", callback_data="assignTeam"),
        ],
    ]
    await update.message.reply_text(
        "Вы хотите зарегистрировать чат для роли или команды?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_TYPE


async def choose_type(update: Update, _):
    query = update.callback_query
    await query.answer()
    selection = query.data

    if selection == "assignRole":
        roles = session.query(Role).all()
        keyboard = [
            [
                InlineKeyboardButton(
                    role.role_name,
                    callback_data=f"chatRole_{role.id}",
                ),
            ]
            for role in roles
        ]
        await query.edit_message_text(
            "Выберите роль:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_ROLE
    if selection == "assignTeam":
        teams = session.query(Team).all()
        keyboard = [
            [
                InlineKeyboardButton(
                    team.name,
                    callback_data=f"chatTeam_{team.id}",
                ),
            ]
            for team in teams
        ]
        await query.edit_message_text(
            "Выберите команду:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_TEAM
    return ConversationHandler.END


async def register_role(update: Update, _):
    query = update.callback_query
    await query.answer()
    role_id = int(query.data.split("_")[1])
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id

    role = session.query(Role).filter_by(id=role_id).first()
    role.chat_id = chat_id
    if thread_id:
        role.thread_id = thread_id
    session.commit()

    await query.edit_message_text(
        f"Группа зарегистрирована для роли {role.role_name}.",
    )
    return ConversationHandler.END


async def register_team(update: Update, _):
    query = update.callback_query
    await query.answer()
    team_id = int(query.data.split("_")[1])
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id

    team = session.query(Team).filter_by(id=team_id).first()
    team.chat_id = chat_id
    if thread_id:
        team.thread_id = thread_id
    session.commit()

    await query.edit_message_text(
        f"Группа зарегистрирована для команды {team.name}.",
    )
    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


register_chat_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("register_chat", start_register)],
    states={
        CHOOSE_TYPE: [
            CallbackQueryHandler(
                choose_type,
                pattern="^(assignRole|assignTeam)$",
            ),
        ],
        CHOOSE_ROLE: [
            CallbackQueryHandler(register_role, pattern="^chatRole_"),
        ],
        CHOOSE_TEAM: [
            CallbackQueryHandler(register_team, pattern="^chatTeam_"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "register_chat_conv",
]
