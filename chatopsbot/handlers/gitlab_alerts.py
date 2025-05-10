import logging

from telegram.error import BadRequest
from telegram.ext import ContextTypes

from database import session
from models import MergeRequest, ServiceSubscription

logger = logging.getLogger(__name__)


async def check_all_merge_requests(context: ContextTypes.DEFAULT_TYPE):
    merge_requests = session.query(
        MergeRequest,
    ).filter_by(acknowledged=False).all()
    for merge_request in merge_requests:
        subscriptions = session.query(
            ServiceSubscription,
        ).filter_by(
            service_id=merge_request.service_id,
        ).all()
        for subscription in subscriptions:
            try:
                if not subscription.is_subscription_active():
                    continue
                await context.bot.send_message(
                    chat_id=subscription.employee_id,
                    text=f"MR {merge_request.title} для сервиса "
                         f"{merge_request.service.name} получил статус merged",
                )
            except BadRequest:
                logger.error("Не удалось отправить сообщение пользователю.")
        try:
            await context.bot.send_message(
                chat_id=merge_request.get_service_chat(),
                text=f"MR {merge_request.title} для сервиса "
                     f"{merge_request.service.name} получил статус merged",
            )
        except BadRequest:
            logger.error(f"Чат {merge_request.name} не найден.")
        finally:
            merge_request.acknowledge()
            session.commit()


__all__ = [
    "check_all_merge_requests",
]
