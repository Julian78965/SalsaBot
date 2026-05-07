# 🌶️ SalsaBot

Tu asistente personal de Telegram que crea eventos en Google Calendar y tareas en Notion automáticamente.

## Archivos en esta carpeta

```
SalsaBot/
├── bot.py              # Bot principal
├── parser.py           # Interpreta tu lenguaje natural
├── google_calendar.py  # Conexión con Google Calendar
├── notion_db.py        # Conexión con Notion
├── setup.py            # Setup inicial (correr una vez)
├── requirements.txt    # Dependencias
├── Procfile            # Para Railway
├── .env                # Tus tokens (NUNCA subir a internet)
└── credentials/
    ├── google_credentials.json  # De Google Cloud
    └── notion_token.txt         # Tu token de Notion
```

## Setup paso a paso

### 1. Crear archivo .env

Copia `.env.example` y renómbralo `.env`. Llena los valores:

```
TELEGRAM_TOKEN=tu_token_de_botfather
NOTION_TOKEN=tu_token_de_notion
AUTHORIZED_USER_ID=tu_id_de_telegram (lo ves cuando haces /start)
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Setup inicial (una sola vez)

```bash
python setup.py
```

Esto autentica Google y crea la base de datos en Notion.

### 4. Correr el bot localmente

```bash
python bot.py
```

### 5. Subir a Railway (para que corra 24/7)

1. Sube la carpeta a GitHub (sin la carpeta credentials/)
2. En Railway, agrega las variables de entorno manualmente
3. Conecta el repo y Railway lo despliega automático

## Ejemplos de uso

```
Feria Eva 7 mayo 7:30AM prioridad 1
Reunión con distribuidor mañana 3PM prioridad 2
Tarea llamar a cliente el viernes prioridad alta
Almuerzo con socio jueves 1PM
```
