from datetime import datetime, timedelta
from collections import Counter
from langchain.tools import tool
from sheets import append_venta, get_ventas_filtradas, get_all_ventas


@tool
def registrar_venta(producto: str, cliente: str, cantidad: int, precio_unitario: float) -> str:
    """
    Registra una nueva venta en la planilla de Google Sheets.
    Usar cuando el usuario mencione que vendió algo.
    Ejemplos: 'vendí una calza a Josefina por $15000', 'anotar venta de remera a Pedro 8000 pesos'.
    El precio_unitario es el precio de una sola unidad, no el total.
    """
    datos = append_venta(producto, cliente, cantidad, precio_unitario)
    total = datos["total"]
    return (
        f"✅ Venta registrada\n"
        f"📦 {datos['cantidad']}x {datos['producto'].capitalize()}\n"
        f"👤 {datos['cliente'].capitalize()}\n"
        f"💰 ${total:,.0f}\n"
        f"📅 {datos['fecha']}"
    )


@tool
def consultar_stats(periodo: str) -> str:
    """
    Devuelve estadísticas de ventas para un periodo determinado.
    Usar cuando el usuario pregunte por sus ventas, ingresos o rendimiento.
    El parámetro periodo solo puede ser: 'hoy', 'semana' o 'mes'.
    Ejemplos: '¿cuánto vendí hoy?', 'resumen de la semana', 'cómo me fue este mes'.
    """
    hoy = datetime.now().strftime("%Y-%m-%d")

    if periodo == "hoy":
        desde = hoy
        hasta = hoy
        label = "hoy"
    elif periodo == "semana":
        desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        hasta = hoy
        label = "los últimos 7 días"
    elif periodo == "mes":
        desde = datetime.now().strftime("%Y-%m-01")
        hasta = hoy
        label = "este mes"
    else:
        return "❌ Periodo no reconocido. Podés preguntar por 'hoy', 'semana' o 'mes'."

    ventas = get_ventas_filtradas(desde=desde, hasta=hasta)

    if not ventas:
        return f"📭 No hay ventas registradas para {label}."

    total_recaudado = sum(v["total"] for v in ventas)
    cantidad_ventas = len(ventas)
    productos = [v["producto"].lower() for v in ventas]
    producto_top = Counter(productos).most_common(1)[0][0]

    return (
        f"📊 Resumen de {label}\n"
        f"🧾 Ventas: {cantidad_ventas}\n"
        f"💰 Total: ${total_recaudado:,.0f}\n"
        f"🏆 Producto más vendido: {producto_top.capitalize()}"
    )


@tool
def listar_clientes() -> str:
    """
    Lista todos los clientes únicos con su cantidad de compras, ordenados de mayor a menor.
    Usar cuando el usuario pregunte por sus clientes.
    Ejemplos: '¿quiénes son mis clientes?', 'listado de clientes', '¿quién me compra más?'.
    """
    ventas = get_all_ventas()

    if not ventas:
        return "📭 No hay ventas registradas todavía."

    conteo = Counter(v["cliente"].capitalize() for v in ventas)
    clientes_ordenados = conteo.most_common()

    lineas = [f"👥 Clientes ({len(clientes_ordenados)} en total)\n"]
    for cliente, compras in clientes_ordenados:
        plural = "compra" if compras == 1 else "compras"
        lineas.append(f"• {cliente}: {compras} {plural}")

    return "\n".join(lineas)