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
from models import Employee, Role
from utils import require_admin

CHOOSE_EMPLOYEE, CHOOSE_NEW_ROLE = range(2)


@require_admin
async def start_change_role(update: Update, _):
    employees = session.query(Employee).all()
    if not employees:
        await update.message.reply_text("Список сотрудников пуст.")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton(
                emp.full_name,
                callback_data=f"changeRole_{emp.id}",
            ),
        ]
        for emp in employees
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите сотрудника для изменения роли:",
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
                callback_data=f"newRole_{role.id}",
            ),
        ]
        for role in roles
    ]
    await query.edit_message_text(
        "Выберите новую роль:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_NEW_ROLE


async def apply_role_update(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    emp_id = context.user_data["employee_id"]
    new_role_id = int(query.data.split("_")[1])

    employee = session.get(Employee, emp_id)

    employee.role_id = new_role_id
    session.commit()

    await query.edit_message_text(
        f"🔄 Роль и команда сотрудника {employee.full_name} обновлены.",
    )
    return ConversationHandler.END


change_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("change_role", start_change_role)],
    states={
        CHOOSE_EMPLOYEE: [
            CallbackQueryHandler(choose_new_role, pattern="^changeRole_"),
        ],
        CHOOSE_NEW_ROLE: [
            CallbackQueryHandler(apply_role_update, pattern="^newRole_"),
        ],
    },
    fallbacks=[],
)


__all__ = [
    "change_conv",
]
