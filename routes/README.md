# Contenido de `routes/`

- `__init__.py`: marca esta carpeta como paquete de Python; no contiene lógica adicional.
- `auth.py`: atiende el inicio y cierre de sesión, verifica las credenciales y crea cuentas nuevas con rol de revendedor.
- `dashboard.py`: calcula y presenta indicadores del panel, como ingresos, ganancias y ventas próximas a vencer.
- `inventory.py`: permite al administrador agregar y consultar elementos de inventario.
- `payments.py`: inicia pagos PSE para ventas y recargas de cartera, y aplica transacciones verificadas por Wompi.
- `products.py`: permite al administrador crear, editar y consultar productos.
- `reseller.py`: permite comprar inventario mayorista con saldo y editar el precio/margen de reventa.
- `README.md`: explica para qué sirve cada archivo de esta carpeta.
- `renewals.py`: registra la renovación de una venta y asigna inventario disponible.
- `reports.py`: calcula y muestra el total y la ganancia de las ventas con pago verificado.
- `sales.py`: registra ventas usando un cliente, un producto y una licencia disponible, y presenta las ventas recientes.
- `users.py`: permite al administrador crear usuarios y consultar las cuentas registradas.
- `wallet.py`: permite consultar movimientos y solicitar recargas de saldo por PSE.
