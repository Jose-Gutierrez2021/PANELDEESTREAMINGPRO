# Contenido de `services/`

- `__init__.py`: expone `notify_customer`, que reúne los intentos de envío por WhatsApp y Telegram.
- `notifications.py`: coordina el envío de un mensaje al cliente por los canales de notificación disponibles.
- `security.py`: genera y valida tokens CSRF para los formularios de ventas y pagos.
- `wompi.py`: inicia transacciones PSE, carga los bancos y valida los eventos firmados de Wompi.
- `README.md`: explica para qué sirve cada archivo de esta carpeta.
- `receipts.py`: crea un diccionario con los datos principales de una venta para usarlo como recibo.
- `telegram.py`: envía mensajes mediante la API de Telegram usando las variables de entorno correspondientes.
- `whatsapp.py`: envía mensajes de texto mediante la API de WhatsApp usando sus variables de entorno.
