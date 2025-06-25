import datetime

from sqlalchemy import func
from telegram import Update
from telegram.ext import CommandHandler

from consts import TIMEZONE
from database import session
from models import Service, ServiceIncident, Team, MergeRequest
from utils import require_admin


def _generate_weekly_incident_report():
    one_week_ago = datetime.datetime.now(
        tz=TIMEZONE,
    ) - datetime.timedelta(days=7)

    incidents = (
        session.query(
            Team.name.label("team_name"),
            func.count(ServiceIncident.id).label("incident_count"),
        )
        .join(Service, Service.team_id == Team.id)
        .join(ServiceIncident, ServiceIncident.service_id == Service.id)
        .filter(ServiceIncident.timestamp >= one_week_ago)
        .group_by(Team.id)
        .order_by(Team.name)
        .all()
    )

    mr_results = (
        session.query(
            Team.name.label("team_name"),
            func.count(MergeRequest.id).label("mr_count"),
        )
        .join(Service, Service.team_id == Team.id)
        .join(MergeRequest, MergeRequest.service_id == Service.id)
        .filter(MergeRequest.timestamp >= one_week_ago)
        .where(MergeRequest.status == "merge")
        .group_by(Team.id)
        .order_by(Team.name)
        .all()
    )

    report_lines = ["📊 Еженедельный отчёт:", "", "🔧 Инциденты:"]

    if incidents:
        for name, count in incidents:
            report_lines.append(f"• {name} — {count} инцидентов")
    else:
        report_lines.append("Нет инцидентов за прошедшую неделю.")

    report_lines.append("")
    report_lines.append("🧩 Merge Requests:")

    if mr_results:
        for name, count in mr_results:
            report_lines.append(f"• {name} — {count} MR")
    else:
        report_lines.append("Нет Merge Requests за прошедшую неделю.")

    return "\n".join(report_lines)


@require_admin
async def send_weekly_report(update: Update, _):
    await update.message.reply_text(
        _generate_weekly_incident_report(),
    )


weekly_report_handler = CommandHandler("weekly_report", send_weekly_report)


__all__ = [
    "weekly_report_handler",
]
