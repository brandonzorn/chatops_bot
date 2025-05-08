from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
)

from database import session
from models import Employee
from utils import require_admin

CHOOSE_EMPLOYEE = 0


@require_admin
async def start_remove_user(update: Update, _):
    employees = session.query(Employee).all()
    if not employees:
        await update.message.reply_text("Список сотрудников пуст.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(emp.full_name, callback_data=f"remove_{emp.id}")]
        for emp in employees
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите сотрудника для удаления:",
        reply_markup=markup,
    )
    return CHOOSE_EMPLOYEE


async def confirm_remove_user(update: Update, _):
    query = update.callback_query
    await query.answer()

    emp_id = int(query.data.split("_")[1])
    employee = session.get(Employee, emp_id)

    if not employee:
        await query.edit_message_text("Сотрудник не найден.")
        return ConversationHandler.END

    session.delete(employee)
    session.commit()
    await query.edit_message_text(f"👤 Сотрудник {employee.full_name} удалён.")
    return ConversationHandler.END


delete_conv = ConversationHandler(
    allow_reentry=True,
    entry_points=[CommandHandler("delete_employee", start_remove_user)],
    states={
        CHOOSE_EMPLOYEE: [
            CallbackQueryHandler(confirm_remove_user, pattern="^remove_"),
        ],
    },
    fallbacks=[],
)


__all__ = [
    "delete_conv",
]
