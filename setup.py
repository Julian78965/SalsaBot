"""
Script de setup - Ejecuta esto UNA SOLA VEZ antes de arrancar el bot.
Hace dos cosas:
1. Autentica tu cuenta de Google (abre el navegador)
2. Crea la base de datos en Notion
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("🌶️ SalsaBot — Setup inicial\n")

# 1. Google Calendar Auth
print("📅 Paso 1: Autenticando Google Calendar...")
print("   Se va a abrir el navegador. Inicia sesión con tu cuenta de Google.")
input("   Presiona Enter cuando estés listo...")

try:
    from google_calendar import get_calendar_service
    service = get_calendar_service()
    print("   ✅ Google Calendar autenticado!\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 2. Notion Database Setup
print("📋 Paso 2: Creando base de datos en Notion...")

notion_token = os.getenv('NOTION_TOKEN')
if not notion_token:
    print("   ❌ NOTION_TOKEN no está en .env")
    print("   Agrega tu token en el archivo .env y vuelve a correr este script.")
else:
    try:
        from notion_db import setup_notion_database
        db_id, error = setup_notion_database()

        if db_id:
            print(f"   ✅ Base de datos creada!")
            print(f"   📝 ID: {db_id}")
            print(f"\n   ⚠️  IMPORTANTE: Agrega esta línea a tu archivo .env:")
            print(f"   NOTION_DATABASE_ID={db_id}")

            # Agregar automáticamente al .env si existe
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    content = f.read()

                if 'NOTION_DATABASE_ID' not in content:
                    with open(env_path, 'a') as f:
                        f.write(f"\nNOTION_DATABASE_ID={db_id}")
                    print(f"   ✅ Agregado automáticamente a .env!")
        else:
            print(f"   ❌ Error: {error}")
            print("   Asegúrate de que tu token de Notion está correcto.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ Setup completado!")
print("🚀 Ahora puedes correr el bot con: python bot.py")
