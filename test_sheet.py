from sheets import append_venta, get_all_ventas, get_ventas_filtradas

# Test 1: escribir una venta
print("--- Test 1: append_venta ---")
resultado = append_venta("calza", "Josefina", 1, 15000)
print("Venta guardada:", resultado)

# Test 2: leer todas las ventas
print("\n--- Test 2: get_all_ventas ---")
ventas = get_all_ventas()
print(f"Total ventas en planilla: {len(ventas)}")
print("Última venta:", ventas[-1])

# Test 3: filtrar por cliente
print("\n--- Test 3: get_ventas_filtradas por cliente ---")
josefina = get_ventas_filtradas(cliente="Josefina")
print(f"Ventas de Josefina: {len(josefina)}")

# Test 4: filtrar por fecha
print("\n--- Test 4: get_ventas_filtradas por fecha ---")
from datetime import datetime
hoy = datetime.now().strftime("%Y-%m-%d")
hoy_ventas = get_ventas_filtradas(desde=hoy, hasta=hoy)
print(f"Ventas de hoy ({hoy}): {len(hoy_ventas)}")