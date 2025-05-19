import logging

from httpx import ConnectError
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, ContextTypes

from consts import ACK_TIMEOUT_MINUTES
from database import session
from integrations.loki_integration import check_service
from models import Service, ServiceIncident, Employee

logger = logging.getLogger(__name__)


async def check_all_services(context: ContextTypes.DEFAULT_TYPE):
    services = session.query(Service).all()
    for service in services:
        try:
            result = await check_service(service)
        except ConnectError:
            logger.error(
                f"Grafana Loki: ошибка подключения сервиса {service.name}",
            )
            continue
        if result <= service.notification_threshold:
            continue
        message_id = None
        try:
            message = await context.bot.send_message(
                chat_id=service.team.chat_id,
                text=f"Превышен порог для сервиса {service.name}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Acknowledge",
                                callback_data=f"ack_{service.id}",
                            ),
                        ],
                    ],
                ),
            )
            message_id = message.message_id

        except BadRequest:
            logger.error(f"Чат {service.name} не найден.")
        finally:
            incident = ServiceIncident(
                service_id=service.id,
                message_id=message_id,
            )
            session.add(incident)
            session.commit()

            context.job_queue.run_once(
                callback=check_acknowledgement,
                when=60 * ACK_TIMEOUT_MINUTES,
                data={"incident_id": incident.id},
            )


async def handle_acknowledge(update: Update, _):
    query = update.callback_query
    await query.answer()

    service_id = int(query.data.split("_")[1])

    incident = session.query(ServiceIncident).filter_by(
        service_id=service_id,
        message_id=query.message.message_id,
    ).first()

    if incident:
        incident.acknowledge()
        session.commit()

    await query.edit_message_text("Инцидент подтвержден.")


async def check_acknowledgement(context: ContextTypes.DEFAULT_TYPE):
    incident_id = context.job.data["incident_id"]

    incident = session.query(ServiceIncident).get(incident_id)
    if not incident or incident.acknowledged:
        return

    incident.acknowledge()
    session.commit()
    team = incident.service.team

    teamlead = session.query(Employee).filter_by(team_id=team.id).first()
    if not teamlead:
        logger.warning(
            f"Не найден тимлид команды {team.name}",
        )
        return

    try:
        await context.bot.send_message(
            chat_id=teamlead.id,
            text=f"⏰ Инцидент по сервису {incident.service.name} "
                 f"не подтвержден в течение {ACK_TIMEOUT_MINUTES} минут.",
        )
    except BadRequest:
        logger.warning(
            f"Не удалось отправить сообщение тимлиду {teamlead.full_name}",
        )


grafana_acknowledge_handler = CallbackQueryHandler(
    handle_acknowledge,
    pattern="^ack_",
)


__all__ = [
    "grafana_acknowledge_handler",
    "check_all_services",
]
