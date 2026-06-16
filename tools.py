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
    Devuelve el total de dinero recaudado, cantidad de ventas y prenda más vendida para un periodo.
    Usar cuando el usuario pregunte por totales, montos, dinero recaudado, ingresos o rendimiento.
    El parámetro periodo solo puede ser: 'hoy', 'semana' o 'mes'.
    Ejemplos: 'dame el total vendido', '¿cuánto recaudé hoy?', 'resumen de la semana', 'cómo me fue este mes'.
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
    Lista todos los clientes únicos rankeados por monto total gastado.
    Usar cuando el usuario pregunte por sus clientes o quiera saber quién le compra más.
    Ejemplos: '¿quiénes son mis clientes?', 'listado de clientes', '¿quién me compra más?'.
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