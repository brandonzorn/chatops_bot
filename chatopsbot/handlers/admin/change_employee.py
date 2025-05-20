from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from database import session
from models import Employee, Role, Team
from utils import require_admin, send_invite_links, remove_from_chats

CHOOSE_EMPLOYEE, CHOOSE_NEW_ROLE, CHOOSE_NEW_TEAM = range(3)


@require_admin
async def start_change_employee(update: Update, _):
    employees = session.query(Employee).all()
    if not employees:
        await update.message.reply_text("Список сотрудников пуст.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                emp.full_name,
                callback_data=f"changeEmp_{emp.id}",
            ),
        ]
        for emp in employees
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите сотрудника для изменения:",
        reply_markup=markup,
    )
    return CHOOSE_EMPLOYEE


async def choose_new_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    emp_id = int(query.data.split("_")[1])
    context.user_data["employee_id"] = emp_id

    roles = session.query(Role).all()
    keyboard = [
        [
            InlineKeyboardButton(
                role.role_name,
                callback_data=f"newEmpRole_{role.id}",
            ),
        ]
        for role in roles
    ]
    await query.edit_message_text(
        "Выберите новую роль:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_NEW_ROLE


async def choose_new_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    new_role_id = int(query.data.split("_")[1])
    context.user_data["new_role_id"] = new_role_id

    teams = session.query(Team).all()
    keyboard = [
        [
            InlineKeyboardButton(
                team.name,
                callback_data=f"newEmpTeam_{team.id}",
            ),
        ]
        for team in teams
    ]
    await query.edit_message_text(
        "Выберите новую команду:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_NEW_TEAM


async def apply_role_update(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    emp_id = context.user_data["employee_id"]
    new_role_id = context.user_data["new_role_id"]
    new_team_id = int(query.data.split("_")[1])

    employee = session.get(Employee, emp_id)

    employee.role_id = new_role_id
    employee.team_id = new_team_id
    session.commit()

    await remove_from_chats(employee, context)
    await send_invite_links(employee, context)

    await query.edit_message_text(
        f"🔄 Роль и команда сотрудника {employee.full_name} обновлены.",
    )
    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


change_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("change_employee", start_change_employee)],
    states={
        CHOOSE_EMPLOYEE: [
            CallbackQueryHandler(choose_new_role, pattern="^changeEmp_"),
        ],
        CHOOSE_NEW_ROLE: [
            CallbackQueryHandler(choose_new_team, pattern="^newEmpRole_"),
        ],
        CHOOSE_NEW_TEAM: [
            CallbackQueryHandler(apply_role_update, pattern="^newEmpTeam_"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


__all__ = [
    "change_conv",
]
