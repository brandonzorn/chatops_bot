import datetime

from sqlalchemy import func
from telegram import Update
from telegram.ext import CommandHandler

from consts import TIMEZONE
from database import session
from models import Service, ServiceIncident


def _generate_weekly_incident_report():
    one_week_ago = datetime.datetime.now(
        tz=TIMEZONE,
    ) - datetime.timedelta(days=7)

    results = (
        session.query(
            Service.name,
            func.count(ServiceIncident.id).label("incident_count"),
        )
        .join(ServiceIncident.service)
        .filter(ServiceIncident.timestamp >= one_week_ago)
        .group_by(Service.id)
        .order_by(Service.name)
        .all()
    )

    report_lines = ["📊 Еженедельный отчёт по инцидентам:", ""]
    for name, count in results:
        report_lines.append(f"• {name} — {count} инцидентов")

    if not results:
        report_lines.append("Инцидентов за неделю не зафиксировано.")

    return "\n".join(report_lines)


async def send_weekly_report(update: Update, _):
    await update.message.reply_text(
        _generate_weekly_incident_report(),
    )


weekly_report_handler = CommandHandler("weekly_report", send_weekly_report)


__all__ = [
    "weekly_report_handler",
]
