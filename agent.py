import os
from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents import create_tool_calling_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from tools import registrar_venta, consultar_stats, listar_clientes
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

# Memoria por número de teléfono (en RAM)
_historiales: dict[int, list] = {}

# Tools disponibles
TOOLS = [registrar_venta, consultar_stats, listar_clientes]

# # LLM
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash",
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0
# )

llm=ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# Prompt del agente
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Sos un asistente de ventas amigable que habla en español rioplatense (usás 'vos' en lugar de 'tú'). "
     "Tu única función es ayudar a registrar ventas y consultar estadísticas usando las tools disponibles. "
     "Siempre confirmá la acción realizada de forma clara y concisa. "
     "Si el mensaje no corresponde a ninguna tool disponible, decí que no entendiste y listá las opciones."),
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
        respuesta = resultado["output"]
    except Exception as e:
        print(f"Error en el agente: {e}")
        respuesta = MENSAJE_FALLBACK

    _actualizar_historial(chat_id, texto, respuesta)
    enviar_mensaje(chat_id, respuesta)