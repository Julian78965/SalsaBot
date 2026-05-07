import re
from datetime import datetime, timedelta
import pytz

BOGOTA_TZ = pytz.timezone('America/Bogota')

MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

DIAS_SEMANA = {
    'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
    'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
}


def detect_command(text):
    text_lower = text.lower().strip()
    if re.match(r'^(borrar|eliminar|cancelar)\s+', text_lower):
        title = re.sub(r'^(borrar|eliminar|cancelar)\s+', '', text, flags=re.IGNORECASE).strip()
        return {'command': 'delete', 'title': title}
    if re.match(r'^(editar|cambiar|modificar)\s+', text_lower):
        title = re.sub(r'^(editar|cambiar|modificar)\s+', '', text, flags=re.IGNORECASE).strip()
        return {'command': 'edit', 'title': title}
    return None


def extract_time(text):
    """Extrae hora del texto. Retorna (hora_str, texto_limpio)."""
    # Formato 7:30AM, 7:30 AM, 7:30am
    match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)', text)
    if match:
        h, m, period = int(match.group(1)), int(match.group(2)), match.group(3).upper()
        if period == 'PM' and h != 12:
            h += 12
        elif period == 'AM' and h == 12:
            h = 0
        clean = text.replace(match.group(0), '').strip()
        return f"{h:02d}:{m:02d}", clean

    # Formato 7AM, 3PM, 7 AM, 3 PM
    match = re.search(r'(\d{1,2})\s*(am|pm|AM|PM)', text)
    if match:
        h, period = int(match.group(1)), match.group(2).upper()
        if period == 'PM' and h != 12:
            h += 12
        elif period == 'AM' and h == 12:
            h = 0
        clean = text.replace(match.group(0), '').strip()
        return f"{h:02d}:00", clean

    # Formato 15:00, 7:30
    match = re.search(r'\b(\d{1,2}):(\d{2})\b', text)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        clean = text.replace(match.group(0), '').strip()
        return f"{h:02d}:{m:02d}", clean

    return None, text


def extract_date(text):
    """Extrae fecha del texto. Retorna (fecha_str YYYY-MM-DD, texto_limpio)."""
    now = datetime.now(BOGOTA_TZ)
    year = now.year

    # Formato: "8 de mayo", "8 mayo"
    match = re.search(r'(\d{1,2})\s+de\s+(' + '|'.join(MESES.keys()) + r')', text, re.IGNORECASE)
    if not match:
        match = re.search(r'(\d{1,2})\s+(' + '|'.join(MESES.keys()) + r')', text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month = MESES[match.group(2).lower()]
        date_str = f"{year}-{month:02d}-{day:02d}"
        clean = text.replace(match.group(0), '').strip()
        return date_str, clean

    # Formato: "8/5" o "8/5/2026"
    match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', text)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        y = int(match.group(3)) if match.group(3) else year
        if y < 100:
            y += 2000
        date_str = f"{y}-{month:02d}-{day:02d}"
        clean = text.replace(match.group(0), '').strip()
        return date_str, clean

    # Relativas
    if re.search(r'\bhoy\b', text, re.IGNORECASE):
        date_str = now.strftime('%Y-%m-%d')
        clean = re.sub(r'\bhoy\b', '', text, flags=re.IGNORECASE).strip()
        return date_str, clean

    if re.search(r'\bmañana\b', text, re.IGNORECASE):
        tomorrow = now + timedelta(days=1)
        date_str = tomorrow.strftime('%Y-%m-%d')
        clean = re.sub(r'\bmañana\b', '', text, flags=re.IGNORECASE).strip()
        return date_str, clean

    # Días de la semana
    for dia, dia_num in DIAS_SEMANA.items():
        if re.search(r'\b' + dia + r'\b', text, re.IGNORECASE):
            days_ahead = dia_num - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target = now + timedelta(days=days_ahead)
            date_str = target.strftime('%Y-%m-%d')
            clean = re.sub(r'\b' + dia + r'\b', '', text, flags=re.IGNORECASE).strip()
            return date_str, clean

    return None, text


def extract_priority(text):
    patterns = [
        (r'prioridad\s*1|prioridad\s*alta|p1\b', 'Alta'),
        (r'prioridad\s*2|prioridad\s*media|p2\b', 'Media'),
        (r'prioridad\s*3|prioridad\s*baja|p3\b', 'Baja'),
    ]
    for pattern, value in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            clean = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            return value, clean
    return 'Media', text


def extract_type(text):
    if re.search(r'\bferia\b|\bevento\b|\blanzamiento\b', text, re.IGNORECASE):
        return 'Evento'
    if re.search(r'\breunion\b|\breunión\b|\bmeeting\b|\bcita\b', text, re.IGNORECASE):
        return 'Reunion'
    if re.search(r'\btarea\b|\btodo\b|\bhacer\b|\bcomprar\b|\bllamar\b|\benviar\b', text, re.IGNORECASE):
        return 'Tarea'
    return 'Evento'


def parse_input(text):
    working = text

    priority, working = extract_priority(working)
    tipo = extract_type(working)
    time_str, working = extract_time(working)
    date_str, working = extract_date(working)

    # Limpiar el título
    title = re.sub(r'\s+', ' ', working).strip()
    title = re.sub(r'^[\W_]+|[\W_]+$', '', title).strip()
    if not title:
        title = text.split()[0].capitalize()

    # Construir datetime si tenemos fecha y hora
    datetime_obj = None
    if date_str and time_str:
        try:
            datetime_obj = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        except:
            pass
    elif date_str:
        try:
            datetime_obj = datetime.strptime(f"{date_str} 09:00", '%Y-%m-%d %H:%M')
        except:
            pass

    return {
        'title': title,
        'date': date_str,
        'time': time_str,
        'datetime_obj': datetime_obj,
        'priority': priority,
        'type': tipo,
        'raw': text
    }


def format_confirmation(parsed):
    emoji_priority = {'Alta': '🔴', 'Media': '🟡', 'Baja': '🟢'}
    emoji_type = {'Evento': '📅', 'Reunion': '🤝', 'Tarea': '✅', 'Personal': '☕'}

    fecha = parsed['date'] if parsed.get('date') else 'No especificada'
    hora = parsed['time'] if parsed.get('time') else 'No especificada'

    lines = [
        f"Creado: {parsed['title']}",
        f"Fecha: {fecha}",
        f"Hora: {hora}",
        f"Prioridad: {emoji_priority.get(parsed['priority'], '')} {parsed['priority']}",
        f"Tipo: {emoji_type.get(parsed['type'], '')} {parsed['type']}",
    ]
    return '\n'.join(lines)
