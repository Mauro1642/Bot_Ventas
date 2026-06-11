import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


def enviar_mensaje(numero: str, texto: str) -> bool:
    """
    Envía un mensaje de texto por WhatsApp.

    Args:
        numero: número del destinatario en formato internacional sin + (ej: 5491112345678)
        texto: mensaje a enviar

    Returns:
        True si se envió correctamente, False si hubo error.
    """
    url = WHATSAPP_API_URL.format(phone_number_id=PHONE_NUMBER_ID)

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return True
    else:
        print(f"Error al enviar mensaje: {response.status_code} - {response.text}")
        return False