import os
from notion_client import Client
from datetime import datetime

def get_notion_client():
    token = os.getenv('NOTION_TOKEN')
    return Client(auth=token)


def find_notion_entries(title_query):
    """Busca entradas en Notion por nombre."""
    try:
        notion = get_notion_client()
        database_id = os.getenv('NOTION_DATABASE_ID')
        results = notion.databases.query(
            database_id=database_id,
            filter={
                "property": "Nombre",
                "title": {"contains": title_query}
            }
        )
        return results.get('results', [])
    except Exception as e:
        return []


def delete_notion_entry(title_query):
    """Archiva (borra) una entrada en Notion por nombre."""
    try:
        entries = find_notion_entries(title_query)
        if not entries:
            return False, "No encontrado"
        
        notion = get_notion_client()
        # Archivar la primera entrada que coincida
        notion.pages.update(page_id=entries[0]['id'], archived=True)
        return True, "Borrado"
    except Exception as e:
        return False, str(e)


def create_notion_entry(parsed):
    """Crea una entrada en la base de datos de Notion."""
    try:
        notion = get_notion_client()
        database_id = os.getenv('NOTION_DATABASE_ID')

        priority_map = {'Alta': '🔴 Alta', 'Media': '🟡 Media', 'Baja': '🟢 Baja'}

        properties = {
            'Nombre': {
                'title': [{'text': {'content': parsed['title']}}]
            },
            'Tipo': {
                'select': {'name': parsed.get('type', 'Evento')}
            },
            'Prioridad': {
                'select': {'name': priority_map.get(parsed.get('priority', 'Media'), '🟡 Media')}
            },
            'Estado': {
                'select': {'name': 'Pendiente'}
            },
        }

        # Agregar fecha si existe
        if parsed.get('date'):
            date_str = parsed['date']
            if parsed.get('time'):
                date_str = f"{parsed['date']}T{parsed['time']}:00"

            properties['Fecha'] = {
                'date': {'start': date_str}
            }

        page = notion.pages.create(
            parent={'database_id': database_id},
            properties=properties
        )

        return True, page['url']

    except Exception as e:
        return False, str(e)


def setup_notion_database():
    """Crea la base de datos de SalsaBot en Notion si no existe."""
    try:
        notion = get_notion_client()

        # Buscar página raíz donde crear la base de datos
        search_results = notion.search(query='', filter={'property': 'object', 'value': 'page'})

        if not search_results['results']:
            return None, "No se encontraron páginas en Notion. Crea una página primero."

        parent_page_id = search_results['results'][0]['id']

        database = notion.databases.create(
            parent={'type': 'page_id', 'page_id': parent_page_id},
            title=[{'type': 'text', 'text': {'content': '🌶️ SalsaBot — Tareas & Eventos'}}],
            properties={
                'Nombre': {'title': {}},
                'Fecha': {'date': {}},
                'Tipo': {
                    'select': {
                        'options': [
                            {'name': 'Evento', 'color': 'blue'},
                            {'name': 'Reunion', 'color': 'green'},
                            {'name': 'Tarea', 'color': 'orange'},
                            {'name': 'Personal', 'color': 'purple'},
                        ]
                    }
                },
                'Prioridad': {
                    'select': {
                        'options': [
                            {'name': '🔴 Alta', 'color': 'red'},
                            {'name': '🟡 Media', 'color': 'yellow'},
                            {'name': '🟢 Baja', 'color': 'green'},
                        ]
                    }
                },
                'Estado': {
                    'select': {
                        'options': [
                            {'name': 'Pendiente', 'color': 'gray'},
                            {'name': 'En progreso', 'color': 'blue'},
                            {'name': 'Completado', 'color': 'green'},
                        ]
                    }
                },
                'Notas': {'rich_text': {}},
            }
        )

        return database['id'], None

    except Exception as e:
        return None, str(e)
