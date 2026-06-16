import os
import json
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def _get_worksheet():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
            scopes=SCOPES
        )
    client = gspread.authorize(creds)
    sheet = client.open(os.getenv("SPREADSHEET_NAME", "VENTAS JF"))
    return sheet.worksheet("VENTAS")


def append_venta(prenda: str, cliente: str, monto: float, metodo_pago: str = "efectivo") -> dict:
    """
    Agrega una fila nueva a la planilla.
    
    Args:
        prenda: descripción de la prenda (ej: "Calza Holanda negra L")
        cliente: nombre del cliente
        monto: monto total de la venta
        metodo_pago: "transferencia" o "efectivo" (default: efectivo)
    
    Returns:
        Diccionario con los datos guardados.
    """
    ws = _get_worksheet()
    dia = datetime.now().strftime("%-d-%b").lower()  # formato: "1-jun"

    transferencia = monto if metodo_pago == "transferencia" else ""
    efectivo = monto if metodo_pago == "efectivo" else ""

    row = [prenda, dia, cliente, transferencia, efectivo]
    ws.append_row(row)

    return {
        "prenda": prenda,
        "dia": dia,
        "cliente": cliente,
        "monto": monto,
        "metodo_pago": metodo_pago
    }


def get_all_ventas() -> list[dict]:
    """
    Devuelve todas las ventas como lista de diccionarios.
    Usa fila 2 como encabezado porque fila 1 es el título.
    """
    ws = _get_worksheet()
    rows = ws.get_all_records(head=2)  # fila 2 como encabezado
    
    # Normalizar keys a minúsculas
    return [{k.lower(): v for k, v in row.items()} for row in rows]


def get_ventas_filtradas(desde: str = None, hasta: str = None, cliente: str = None) -> list[dict]:
    """
    Filtra ventas por rango de fechas y/o cliente.

    Args:
        desde: fecha inicio en formato YYYY-MM-DD (opcional)
        hasta: fecha fin en formato YYYY-MM-DD (opcional)
        cliente: nombre del cliente, case-insensitive (opcional)

    Returns:
        Lista de ventas que cumplen los filtros.
    """
    ventas = get_all_ventas()

    if desde:
        ventas = [v for v in ventas if v["día"] >= desde]

    if hasta:
        ventas = [v for v in ventas if v["día"] <= hasta]

    if cliente:
        ventas = [v for v in ventas if v["nombre"].lower() == cliente.lower()]

    return ventas