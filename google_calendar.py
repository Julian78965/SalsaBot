import os
import json
import pickle
import tempfile
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
BOGOTA_TZ = pytz.timezone('America/Bogota')
CREDENTIALS_FILE = 'Credenciales/Google_Credentials.json'
TOKEN_FILE = 'Credenciales/google_token.pkl'


def get_calendar_service():
    """Autentica y retorna el servicio de Google Calendar."""
    creds = None

    # En Railway, usar token desde variable de entorno
    token_env = os.getenv('GOOGLE_TOKEN_JSON')
    if token_env:
        try:
            token_data = json.loads(token_env)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error cargando token desde env: {e}")

    # En local, usar archivo pickle
    if not creds and os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Verificar si hay credentials en variable de entorno (Railway)
            creds_env = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_env:
                # En Railway no podemos abrir navegador, retornar error claro
                raise Exception("Google Calendar necesita autenticación inicial. Corre setup.py localmente primero y agrega GOOGLE_TOKEN_JSON a Railway.")
            
            # Local: autenticar con archivo
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Guardar token
        if os.path.exists(os.path.dirname(TOKEN_FILE)):
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_token_json():
    """Retorna el token como JSON string para guardar en Railway."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
        return creds.to_json()
    return None


def find_events(title_query):
    """Busca eventos en Google Calendar por nombre."""
    try:
        service = get_calendar_service()
        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime',
            q=title_query
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        return []


def delete_event(event_id):
    """Borra un evento de Google Calendar por ID."""
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True, "Borrado"
    except Exception as e:
        return False, str(e)


def create_event(parsed):
    """Crea un evento en Google Calendar."""
    try:
        service = get_calendar_service()

        if parsed.get('datetime_obj'):
            start_dt = parsed['datetime_obj']
        else:
            tomorrow = datetime.now(BOGOTA_TZ) + timedelta(days=1)
            start_dt = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).replace(tzinfo=None)

        end_dt = start_dt + timedelta(hours=1)

        color_map = {'Alta': '11', 'Media': '5', 'Baja': '2'}
        color_id = color_map.get(parsed.get('priority', 'Media'), '5')

        event = {
            'summary': parsed['title'],
            'description': f"Tipo: {parsed['type']}\nPrioridad: {parsed['priority']}\nCreado por SalsaBot",
            'start': {
                'dateTime': start_dt.strftime('%Y-%m-%dT%H:%M:00'),
                'timeZone': 'America/Bogota',
            },
            'end': {
                'dateTime': end_dt.strftime('%Y-%m-%dT%H:%M:00'),
                'timeZone': 'America/Bogota',
            },
            'colorId': color_id,
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': 30}],
            },
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return True, created_event.get('htmlLink')

    except Exception as e:
        return False, str(e)

