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
    ws = _get_worksheet()
    
    headers = [h.lower() for h in ws.row_values(2)]
    all_rows = ws.get_all_values()[2:]

    year = int(os.getenv("SHEET_YEAR", datetime.now().year))
    month = int(os.getenv("SHEET_MONTH", datetime.now().month))

    meses = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4,
        "may": 5, "jun": 6, "jul": 7, "ago": 8,
        "sep": 9, "oct": 10, "nov": 11, "dic": 12
    }

    def parsear_fecha(valor: str) -> str:
        """Convierte '1-jun' a '2026-06-01'"""
        try:
            partes = valor.strip().split("-")
            dia = int(partes[0])
            mes = meses.get(partes[1].lower(), month)
            return f"{year}-{mes:02d}-{dia:02d}"
        except:
            return ""

    result = []
    for row in all_rows:
        if any(cell.strip() for cell in row):
            fila = dict(zip(headers, row))
            # Convertir la columna día al formato estándar
            if "día" in fila:
                fila["día"] = parsear_fecha(fila["día"])
            result.append(fila)

    return result


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