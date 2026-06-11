import time
from telegram import obtener_mensajes,enviar_mensaje
from agent import procesar_mensaje

def main():
    print("Bot iniciado, esperando mensajes...")
    
    # Obtener el offset actual para ignorar mensajes anteriores
    updates = obtener_mensajes()
    offset = updates[-1]["update_id"] + 1 if updates else None

    print("Listo, esperando mensajes nuevos...")

    while True:
        mensajes = obtener_mensajes(offset)

        for update in mensajes:
            offset = update["update_id"] + 1

            if "message" not in update:
                continue
            if "text" not in update["message"]:
                continue

            chat_id = update["message"]["chat"]["id"]
            texto = update["message"]["text"]
            if texto == "/start":
                enviar_mensaje(
                    chat_id,
                    "¡Hola Ju! Bienvenida a tu bot, podes pedirme cosas como:\n\n"
                    "- Registrar ventas\n"
                    "- Consultar estadísticas de ventas\n"
                    "- Ver estadísticas de tus clientes\n\n"
                    " Que tengas un lindo dia 😊"
                )
                continue
            print(f"Mensaje recibido de {chat_id}: {texto}")
            procesar_mensaje(chat_id, texto)

        time.sleep(1)

if __name__ == "__main__":
    main()