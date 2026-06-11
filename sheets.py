import os
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
    creds = Credentials.from_service_account_file(
        os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open(os.getenv("SPREADSHEET_NAME", "Ventas_bot"))
    return sheet.worksheet("ventas")

def append_venta(producto: str, cliente: str, cantidad: int, precio_unitario: float) -> dict:
    """Agrega una fila nueva a la planilla. Devuelve los datos guardados."""
    ws = _get_worksheet()
    fecha = datetime.now().strftime("%Y-%m-%d")
    total = cantidad * precio_unitario
    row = [fecha, producto, cliente, cantidad, precio_unitario, total]
    ws.append_row(row)
    return {
        "fecha": fecha,
        "producto": producto,
        "cliente": cliente,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
        "total": total
    }

def get_all_ventas() -> list[dict]:
    """Devuelve todas las ventas como lista de diccionarios."""
    ws = _get_worksheet()
    rows = ws.get_all_records()  # usa la fila 1 como keys automáticamente
    return rows

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
        ventas = [v for v in ventas if v["fecha"] >= desde]
 
    if hasta:
        ventas = [v for v in ventas if v["fecha"] <= hasta]
 
    if cliente:
        ventas = [v for v in ventas if v["cliente"].lower() == cliente.lower()]
 
    return ventas