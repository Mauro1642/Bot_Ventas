import os
from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents import create_tool_calling_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from tools import registrar_venta, consultar_stats, listar_clientes, buscar_ventas_cliente
from telegram import enviar_mensaje

load_dotenv()

MENSAJE_FALLBACK = (
    "❓ No entendí ese mensaje.\n\n"
    "Estas son las cosas que puedo hacer:\n"
    "• Registrar una venta → 'Vendí una calza a Josefina por $15000'\n"
    "• Ver stats de hoy → '¿Cuánto vendí hoy?'\n"
    "• Ver stats de la semana → '¿Cuánto vendí esta semana?'\n"
    "• Ver stats del mes → '¿Cómo me fue este mes?'\n"
    "• Ver clientes → '¿Quiénes son mis clientes?'\n\n"
    "¿Necesitás algo que no está en la lista? Escribile a Mauro y lo agrega 😊"
)

# Memoria por chat_id (en RAM)
_historiales: dict[int, list] = {}

# Tools disponibles
TOOLS = [registrar_venta, consultar_stats, listar_clientes,buscar_ventas_cliente]

from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(
    model="claude-haiku-4-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0
)


# Prompt del agente
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Sos un asistente de ventas amigable que habla en español rioplatense (usás 'vos' en lugar de 'tú'). "
     "Tu única función es ayudar a registrar ventas y consultar estadísticas usando las tools disponibles. "
     "Las ventas tienen: prenda (descripción completa incluyendo modelo, color y talle), cliente (nombre), "
     "monto (precio total) y metodo_pago ('efectivo' o 'transferencia', por defecto 'efectivo'). "
     "Siempre confirmá la acción realizada de forma clara y concisa."
     "Cuando una tool devuelva una lista o datos, mostrá TODOS los items exactamente como vienen, uno por línea, sin resumir ni omitir ninguno."
     "IMPORTANTE: Cuando una tool devuelva datos, mostrá el resultado COMPLETO y EXACTO tal como lo devuelve la tool, sin resumir, sin parafrasear y sin omitir nada. "
     "No agregues frases como 'acabo de darte' o 'se ha listado' — simplemente mostrá los datos."
     "IMPORTANTE: Siempre ejecutá la tool correspondiente cuando el usuario la pida, incluso si ya la ejecutaste antes. "
     "Nunca digas que ya diste una respuesta anteriormente — siempre volvé a ejecutar la tool y mostrá los datos actualizados. "
     "Si el mensaje no corresponde a ninguna tool disponible, decí que no entendiste y listá las opciones."
     "Siempre enviale al usuario por chat las respuestas que generes, no importa si son largas o cortas. "),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
# Agente
agent = create_tool_calling_agent(llm, TOOLS, prompt)
agent_executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True)


def _get_historial(chat_id: int) -> list:
    """Devuelve el historial de conversación para un número."""
    if chat_id not in _historiales:
        _historiales[chat_id] = []
    return _historiales[chat_id]


def _actualizar_historial(chat_id: int, mensaje_usuario: str, respuesta: str):
    """Agrega el intercambio al historial."""
    historial = _get_historial(chat_id)
    historial.append(HumanMessage(content=mensaje_usuario))
    historial.append(AIMessage(content=respuesta))

    # Limitar a los últimos 20 mensajes (10 intercambios) para no crecer indefinidamente
    if len(historial) > 20:
        _historiales[chat_id] = historial[-20:]


def procesar_mensaje(chat_id: int, texto: str):
    """
    Procesa un mensaje entrante de Telegram y envía la respuesta.

    Args:
        chat_id: chat_id del usuario en telegram
        texto: contenido del mensaje
    """
    historial = _get_historial(chat_id)

    try:
        resultado = agent_executor.invoke({
            "input": texto,
            "chat_history": historial
        })
        # Claude Haiku a veces devuelve lista de bloques en vez de string
        output = resultado["output"]
        if isinstance(output, list):
            respuesta = " ".join(
                bloque.get("text", "") for bloque in output
                if isinstance(bloque, dict) and bloque.get("type") == "text"
            )
        else:
            respuesta = output
    except Exception as e:
        print(f"Error en el agente: {e}")
        respuesta = MENSAJE_FALLBACK

    _actualizar_historial(chat_id, texto, respuesta)
    enviar_mensaje(chat_id, respuesta)