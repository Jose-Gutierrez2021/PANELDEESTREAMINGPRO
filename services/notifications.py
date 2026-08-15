from .telegram import send_telegram
from .whatsapp import send_whatsapp


def notify_customer(
    phone,
    message
):

    whatsapp = send_whatsapp(
        phone,
        message
    )

    telegram = send_telegram(
        message
    )

    return {
        "whatsapp": whatsapp,
        "telegram": telegram
    }
