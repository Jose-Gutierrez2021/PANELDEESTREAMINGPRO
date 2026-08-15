import os
import requests


def send_whatsapp(phone, message):

    token = os.getenv(
        "WHATSAPP_ACCESS_TOKEN"
    )

    phone_number_id = os.getenv(
        "WHATSAPP_PHONE_NUMBER_ID"
    )

    if not token or not phone_number_id:

        return False

    url = (
        "https://graph.facebook.com/v23.0/"
        f"{phone_number_id}/messages"
    )

    headers = {
        "Authorization":
            f"Bearer {token}",

        "Content-Type":
            "application/json"
    }

    data = {
        "messaging_product": "whatsapp",

        "to": phone,

        "type": "text",

        "text": {
            "body": message
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=10
    )

    return response.ok
