from tools import registrar_venta, consultar_stats, listar_clientes

print(registrar_venta.invoke({"producto": "remera", "cliente": "Pedro", "cantidad": 2, "precio_unitario": 8000}))
print()
print(consultar_stats.invoke({"periodo": "hoy"}))
print()
print(consultar_stats.invoke({"periodo": "mes"}))
print()
print(listar_clientes.invoke({}))