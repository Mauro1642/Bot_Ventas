from datetime import datetime, timedelta
from collections import Counter
from langchain.tools import tool
from sheets import append_venta, get_ventas_filtradas, get_all_ventas


@tool
def registrar_venta(prenda: str, cliente: str, monto: float, metodo_pago: str = "efectivo") -> str:
    """
    Registra una nueva venta en la planilla de Google Sheets.
    Usar cuando el usuario mencione que vendió algo.
    Ejemplos: 'vendí una calza holanda negra L a Josefina por $15000 en efectivo', 'anotar venta de top Milan azul M a Pedro, $8000, transferencia'.
    El parámetro metodo_pago solo puede ser 'efectivo' o 'transferencia'. Si no se menciona, preguntarle al usuario cual fue el metodo de pago.
    """
    datos = append_venta(prenda, cliente, monto, metodo_pago)
    return (
        f"✅ Venta registrada\n"
        f"👗 {datos['prenda'].capitalize()}\n"
        f"👤 {datos['cliente'].capitalize()}\n"
        f"💰 ${datos['monto']:,.0f} ({datos['metodo_pago']})\n"
        f"📅 {datos['dia']}"
    )


def _calcular_total_venta(venta: dict) -> float:
    """Suma transferencia + efectivo para obtener el total de una venta."""
    def limpiar_monto(valor) -> float:
        if not valor:
            return 0
        try:
            # Eliminar $, puntos de miles y reemplazar coma decimal por punto
            limpio = str(valor).replace("$", "").replace(".", "").replace(",", ".").strip()
            return float(limpio) if limpio else 0
        except (ValueError, TypeError):
            return 0

    return limpiar_monto(venta.get("transferencia")) + limpiar_monto(venta.get("efectivo"))


@tool
def consultar_stats(periodo: str) -> str:
    """
    Devuelve el total de dinero recaudado, cantidad de ventas y prenda más vendida para un periodo de tiempo.
    Usar ÚNICAMENTE cuando el usuario pregunte por montos, totales, dinero o rendimiento en un periodo.
    NUNCA usar para preguntas sobre clientes o listados.
    El parámetro periodo solo puede ser: 'hoy', 'semana' o 'mes'.
    Ejemplos: '¿cuánto recaudé hoy?', 'resumen de la semana', 'cómo me fue este mes', 'total vendido'.
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

    total_recaudado = sum(_calcular_total_venta(v) for v in ventas)
    cantidad_ventas = len(ventas)
    prendas = [v["prendas"].lower() for v in ventas if v.get("prendas")]
    prenda_top = Counter(prendas).most_common(1)[0][0] if prendas else "N/A"

    return (
        f"📊 Resumen de {label}\n"
        f"🧾 Ventas: {cantidad_ventas}\n"
        f"💰 Total: ${total_recaudado:,.0f}\n"
        f"🏆 Prenda más vendida: {prenda_top.capitalize()}"
    )


@tool
def listar_clientes() -> str:
    """
    Lista todos los clientes únicos rankeados por monto total gastado con cantidad de compras.
    Usar ÚNICAMENTE cuando el usuario pida ver clientes, listado de clientes o quiera saber quién compra más.
    NUNCA usar para preguntas sobre montos o estadísticas de ventas.
    Ejemplos: '¿quiénes son mis clientes?', 'listado de clientes', '¿quién me compra más?', 'dame la lista de clientes'.
    """
    ventas = get_all_ventas()

    if not ventas:
        return "📭 No hay ventas registradas todavía."

    # Agrupar por cliente
    clientes: dict[str, dict] = {}
    for v in ventas:
        nombre = v.get("nombre", "").capitalize()
        if not nombre:
            continue
        if nombre not in clientes:
            clientes[nombre] = {"compras": 0, "total": 0}
        clientes[nombre]["compras"] += 1
        clientes[nombre]["total"] += _calcular_total_venta(v)

    # Ordenar por monto total
    clientes_ordenados = sorted(clientes.items(), key=lambda x: x[1]["total"], reverse=True)

    lineas = [f"👥 Clientes ({len(clientes_ordenados)} en total)\n"]
    for i, (nombre, datos) in enumerate(clientes_ordenados, 1):
        plural = "compra" if datos["compras"] == 1 else "compras"
        lineas.append(
            f"{i}. {nombre}\n"
            f"   💰 ${datos['total']:,.0f} | 🧾 {datos['compras']} {plural}"
        )

    return "\n".join(lineas)

@tool
def buscar_ventas_cliente(cliente: str) -> str:
    """
    Muestra todas las compras de un cliente específico con fecha, prenda y monto.
    Usar cuando el usuario pregunte por las compras de una persona en particular.
    Ejemplos: 'listame las compras de Julieta Olague', '¿qué le vendí a Vanesa?', 'historial de Josefina'.
    """
    ventas = get_ventas_filtradas(cliente=cliente)

    if not ventas:
        return f"📭 No hay ventas registradas para {cliente.capitalize()}."

    total = sum(_calcular_total_venta(v) for v in ventas)
    lineas = [f"🛍️ Compras de {cliente.capitalize()} ({len(ventas)} en total | 💰 ${total:,.0f})\n"]

    for v in ventas:
        monto = _calcular_total_venta(v)
        lineas.append(f"• {v.get('día', '')} | {v.get('prendas', '')} | ${monto:,.0f}")

    return "\n".join(lineas)