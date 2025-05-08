import datetime
import logging

from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes

from chatopsbot.config import BOT_TOKEN
from database import session
from handlers.admin import (
    register_chat_conv,
    review_conv,
    delete_conv,
    change_conv,
    threshold_conv,
)
from handlers.notifications import subscribe_conv, silence_handler
from handlers.registration import registration_conv

__all__ = []

from integrations.loki_integration import check_service

from models import Service

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def check_all_services(context: ContextTypes.DEFAULT_TYPE):
    services = session.query(Service).all()
    for service in services:
        result = await check_service(service)
        if result > service.notification_threshold:
            try:
                await context.bot.send_message(
                    chat_id=service.team.chat_id,
                    text=f"Превышен порог для сервиса {service.name}",
                )
            except BadRequest:
                logger.error(f"Чат {service.name} не найден.")


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_repeating(
        check_all_services,
        datetime.timedelta(minutes=10),
        name="check_services",
    )

    application.add_handler(registration_conv)
    application.add_handler(subscribe_conv)
    application.add_handler(silence_handler)

    # admin
    application.add_handler(register_chat_conv)
    application.add_handler(review_conv)
    application.add_handler(delete_conv)
    application.add_handler(change_conv)
    application.add_handler(threshold_conv)

    application.run_polling()


if __name__ == "__main__":
    main()
