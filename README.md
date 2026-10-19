# Panel de streaming

Guía de los archivos y carpetas que hay en la raíz del proyecto. Cada carpeta tiene, además, su propio `README.md` con el detalle de su contenido.

## Carpetas

- `instance/`: base de datos local y archivos de instancia; su README describe cada elemento.
- `models/`: clases que representan los datos de la aplicación en la base de datos.
- `routes/`: controladores y endpoints HTTP organizados por función.
- `services/`: funciones reutilizables para notificaciones, seguridad y pagos.
- `templates/`: páginas HTML que Flask presenta en el navegador.

## Archivos

- `.env`: configuración local y valores privados de ejecución. No compartir ni publicar su contenido.
- `.env.example`: plantilla de variables de entorno necesarias para ejecutar e integrar la aplicación, sin valores secretos reales.
- `.gitignore`: indica a Git qué archivos locales o generados debe ignorar y permite conservar `instance/README.md`.
- `app.py`: crea y configura la aplicación Flask, registra las rutas, inicializa las tablas y expone la comprobación `/health`.
- `config.py`: carga variables de entorno y configura la clave secreta y la conexión a la base de datos.
- `create_structure.py`: abre la aplicación y muestra los productos registrados en la base de datos; no crea carpetas.
- `extensions.py`: crea la instancia compartida de SQLAlchemy que usan los modelos y las rutas.
- `list_products.py`: agrega productos iniciales de servicios de streaming y música cuando todavía no existen.
- `Procfile`: indica a plataformas compatibles que inicien la aplicación con Gunicorn.
- `README.md`: explica para qué sirve cada archivo y carpeta de la raíz del proyecto.
- `dev-monitor.js`: monitor Node para ver cambios de archivos y medir la latencia de Flask durante el desarrollo.
- `package.json`: define el comando `npm run dev` para iniciar el monitor Node.
- `../PANEL STREAMING-backup/latest/`: copia local completa más reciente del proyecto, creada y reemplazada por el monitor Node.
- `render.yaml`: configura el servicio web de Render, sus comandos de instalación e inicio y algunas variables de entorno.
- `requirements.txt`: lista las dependencias de Python necesarias para la aplicación.
- `services/wompi.py`: inicia y verifica pagos PSE de Wompi, manteniendo las llaves privadas en el servidor.
- `services/product_brands.py`: asocia los servicios de streaming y música con los dominios de sus logos y colores de marca.
- `services/security.py`: crea y valida tokens CSRF en las acciones de ventas y pagos.
- `static/js/product-brands.js`: muestra monogramas de respaldo si no carga un logo de marca.
- `static/js/sales.js`: actualiza el total según el producto seleccionado en ventas.
- `seed_products.py`: cambia a 30 días la duración de los productos cuyo proveedor es “Streaming”.
- `show_music_durations.py`: muestra el identificador, nombre y duración de cada producto de música.
- `show_streaming_durations.py`: muestra el identificador, nombre y duración de cada producto de streaming.
- `update_music_duration.py`: cambia a 30 días la duración de los productos cuyo proveedor es “Música” o “Musica”.
- `update_streaming_duration.py`: cambia a 30 días la duración de los productos cuyo proveedor es “Streaming”.
- `vercel.json`: indica a Vercel que construya la aplicación Python desde `app.py` y dirija las solicitudes a ella.

## Configuración inicial y despliegue

Para crear el primer administrador, configura `ADMIN_USERNAME` y
`ADMIN_PASSWORD` en el entorno o en `.env`. La contraseña debe tener al menos
12 caracteres; la aplicación ya no crea una cuenta con una contraseña
predeterminada. Configura también un `SECRET_KEY` aleatorio y estable para
conservar las sesiones entre reinicios. Nunca publiques `.env` ni agregues
secretos al repositorio.

Vercel no conserva una base de datos SQLite local entre ejecuciones. Para
desplegar la aplicación funcionalmente, configura una base PostgreSQL externa
en `DATABASE_URL` junto con `SECRET_KEY`, `ADMIN_USERNAME` y `ADMIN_PASSWORD`
en las variables privadas del proyecto de Vercel antes del primer despliegue.
Los archivos locales de `static/music/` se excluyen de Git; añade únicamente
audio para el que tengas derechos de redistribución.

La sección y las rutas de administración de clientes se retiraron. Los registros y el modelo se conservan en la base de datos porque las ventas existentes dependen de ellos.

## Pagos PSE con Wompi

Las ventas nuevas y las renovaciones usan únicamente PSE. El pagador selecciona su banco en el formulario, y Wompi deposita los pagos en la cuenta bancaria configurada en el comercio Wompi; no se almacena información bancaria en esta aplicación. Una venta solo queda verificada después de validar la transacción consultada directamente en Wompi. La URL de retorno del navegador no confirma por sí sola un pago.

## Cartera y compra para reventa

Las cuentas de revendedor creadas desde el registro pueden abrir **Reventa** para comprar unidades con saldo prepago; las cuentas de administrador configuran el precio mayorista y el margen sugerido de cada producto desde **Productos**. La recomendación inicial es un margen del 40 %. El revendedor puede editar su margen o precio de venta sugerido, consultar las unidades asignadas a su cuenta y venderlas por fuera de StreamPanel. El rol de revendedor no tiene acceso al historial ni a las métricas globales de ventas; los vendedores existentes conservan sus permisos.

La cartera se recarga por PSE con un mínimo de $10.000 COP. El saldo solo se acredita tras validar el evento firmado y consultar la transacción directamente con Wompi. Las compras descuentan el saldo y asignan inventario disponible en una sola operación; los movimientos de cartera quedan registrados. Se requiere la misma configuración de Wompi y webhook descrita arriba para habilitar las recargas.

Para activar el flujo:

1. Crea el comercio en [Wompi Comercios](https://comercios.wompi.co) y configura allí la única cuenta receptora.
2. Copia las llaves `pub_test_`, `prv_test_`, `test_integrity_` y `test_events_` en el archivo `.env` local para pruebas. No las publiques, no las agregues a Git y no las compartas en el chat.
3. Configura en el panel Wompi la URL de eventos `https://TU-DOMINIO/payments/wompi/webhook` y establece `WOMPI_REDIRECT_URL=https://TU-DOMINIO/payments/wompi/result` en `.env`. Wompi debe poder acceder a la URL de eventos por HTTPS para notificar transacciones y el servidor las valida con el secreto de eventos.
4. Prueba en sandbox. Para pasar a dinero real, cambia `WOMPI_ENVIRONMENT=production` y reemplaza todas las llaves por sus equivalentes `pub_prod_`, `prv_prod_`, `prod_integrity_` y `prod_events_`.

El archivo `.env.example` muestra las variables. Sin llaves válidas, el formulario de ventas queda deshabilitado para evitar aceptar pedidos como si PSE estuviera conectado. Wompi requiere consentimiento explícito de términos y tratamiento de datos, y el formulario obtiene los enlaces vigentes de su API. El entorno local `127.0.0.1` no puede recibir webhooks externos; se necesita un dominio HTTPS público para completar las pruebas de notificación.

## Desarrollo con monitor Node

Inicia el monitor desde la terminal integrada de VS Code:

```powershell
npm run dev
```

Node comprueba `/health` y `/login` cada cinco segundos y muestra sus códigos HTTP y tiempos de respuesta. Una respuesta de hasta 500 ms aparece como `OK`; una más lenta se marca como `LENTO`. También informa de archivos Python, HTML, CSS, JavaScript y JSON que cambien. Si Flask ya está en ejecución, el monitor se conecta a él; si no, inicia `app.py`. Mantén esa terminal abierta para seguir viendo las mediciones y usa `Ctrl+C` para detener el monitor.

Cada cambio de archivo se imprime con hora, tipo de cambio y ruta relativa al proyecto.
Si Node inició Flask, los cambios Python reinician ese proceso para aplicar el código; si el monitor se conectó a un servidor iniciado aparte, solo reporta el cambio y deja su recarga en manos de ese servidor.

Al iniciar el monitor, Node guarda una copia completa del proyecto y repite la operación cada dos horas mientras siga abierto. Las copias se guardan fuera de la carpeta del proyecto, en `../PANEL STREAMING-backup/latest/`, incluyen los archivos ocultos y locales (por ejemplo, `.env`, `.git`, entornos virtuales y la base de datos), y reemplazan la versión anterior solo después de completar la nueva. Si una copia falla, el monitor muestra el error y conserva la anterior. Mantén abierta la tarea de VS Code para que se ejecute el siguiente intervalo.

Se puede cambiar el destino con `MONITOR_URL` o el intervalo con `MONITOR_INTERVAL_MS` (mínimo 1000 ms). Por ejemplo:

```powershell
$env:MONITOR_URL = "http://127.0.0.1:5000/"
$env:MONITOR_INTERVAL_MS = "3000"
npm run dev
```
