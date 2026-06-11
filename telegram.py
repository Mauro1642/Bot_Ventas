import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def enviar_mensaje(chat_id: int, texto: str) -> bool:
    """
    Envía un mensaje de texto por Telegram.

    Args:
        chat_id: identificador del chat
        texto: mensaje a enviar

    Returns:
        True si se envió correctamente, False si hubo error.
    """
    response = requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": texto}
    )

    if response.status_code == 200:
        return True
    else:
        print(f"Error al enviar mensaje: {response.status_code} - {response.text}")
        return False

def obtener_mensajes(offset: int = None) -> list:
    """
    Obtiene los mensajes pendientes (para polling en desarrollo).

    Args:
        offset: id del último mensaje procesado + 1

    Returns:
        Lista de updates de Telegram.
    """
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset

    response = requests.get(f"{BASE_URL}/getUpdates", params=params)

    if response.status_code == 200:
        return response.json().get("result", [])
    else:
        print(f"Error al obtener mensajes: {response.status_code} - {response.text}")
        return []