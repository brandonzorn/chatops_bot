import datetime
import logging

from telegram.ext import Application

from config import BOT_TOKEN
from handlers.admin import (
    add_role_handler,
    add_team_conv,
    register_chat_conv,
    review_conv,
    delete_conv,
    change_conv,
    threshold_conv,
)
from handlers.alerts import acknowledge_handler, check_all_services
from handlers.notifications import subscribe_conv, silence_handler
from handlers.registration import registration_conv

__all__ = []

from handlers.reports import weekly_report_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


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
    application.add_handler(acknowledge_handler)
    application.add_handler(weekly_report_handler)

    # admin
    application.add_handler(add_role_handler)
    application.add_handler(add_team_conv)
    application.add_handler(register_chat_conv)
    application.add_handler(review_conv)
    application.add_handler(delete_conv)
    application.add_handler(change_conv)
    application.add_handler(threshold_conv)

    application.run_polling()


if __name__ == "__main__":
    main()
