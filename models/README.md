# Contenido de `models/`

- `__init__.py`: importa los modelos para que puedan localizarse desde el paquete `models`.
- `customer.py`: define `Customer`, con nombre, teléfono, correo, notas y fecha de creación del cliente.
- `inventory.py`: define `Inventory`, con el producto asociado, la referencia, el estado y la fecha de vencimiento de cada elemento.
- `payment.py`: define `Payment`, que registra el importe, método, referencia, estado y fecha de un pago asociado a una venta.
- `product.py`: define `Product`, con nombre, proveedor, duración, precio de venta, costo y estado activo.
- `reseller.py`: registra compras mayoristas, unidades asignadas a cada revendedor y precios/márgenes individuales de reventa.
- `README.md`: explica para qué sirve cada archivo de esta carpeta.
- `sale.py`: define `Sale`, que relaciona cliente, producto, inventario y vendedor, y registra fechas, importes y estados de venta y pago.
- `user.py`: define `User`, incluidos nombre, usuario, contraseña protegida mediante hash, rol y estado; también implementa la comprobación de contraseña.
- `wallet.py`: almacena saldos, recargas PSE y movimientos de cartera para auditar abonos y compras.
- `wholesale.py`: guarda el precio mayorista y el margen de reventa recomendado por producto.
