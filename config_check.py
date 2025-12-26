"""
ChatDT - Fase 1: Configuracion y verificacion de la API

Este script verifica la conexion con API-FOOTBALL y obtiene:
- El ID de la Liga Profesional Argentina
- La lista de equipos de la temporada actual

Ejecutar: python config_check.py
"""

import os
import sys
from dotenv import load_dotenv
import requests

# Cargar variables de entorno desde .env
load_dotenv()

# Configuracion de la API
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

# IMPORTANTE: El plan gratuito solo permite temporadas 2021-2023
# Usamos 2023 como la mas reciente disponible
FREE_PLAN_SEASON = 2023

# Headers requeridos por la API
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}


def check_api_key():
    """Verifica que la API key este configurada."""
    if not API_KEY:
        print("ERROR: No se encontro API_FOOTBALL_KEY en el archivo .env")
        print("Pasos para solucionarlo:")
        print("1. Copia .env.example a .env")
        print("2. Obtene tu API key en https://dashboard.api-football.com")
        print("3. Reemplaza 'tu_api_key_aqui' con tu key real")
        sys.exit(1)
    print(f"API Key configurada: {API_KEY[:8]}...")


def get_argentina_leagues():
    """
    Obtiene las ligas de Argentina que estan activas actualmente.
    Endpoint: GET /leagues
    """
    url = f"{BASE_URL}/leagues"
    params = {
        "country": "Argentina",
        "current": "true"
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"ERROR: La API respondio con codigo {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    
    # Verificar errores de la API
    if data.get("errors"):
        print(f"ERROR de API: {data['errors']}")
        sys.exit(1)
    
    return data["response"]


def find_liga_profesional(leagues):
    """
    Busca la Liga Profesional Argentina en la lista de ligas.
    Generalmente tiene el ID 128.
    """
    liga_profesional = None
    
    print("\n--- Ligas de Argentina encontradas ---")
    for league_data in leagues:
        league = league_data["league"]
        seasons = league_data.get("seasons", [])
        current_season = next((s for s in seasons if s.get("current")), None)
        
        print(f"  - {league['name']} (ID: {league['id']})")
        
        # Buscar la Liga Profesional (puede llamarse "Liga Profesional Argentina" o similar)
        if "profesional" in league["name"].lower() or league["id"] == 128:
            # Usar temporada del plan gratuito en lugar de la actual
            api_season = current_season["year"] if current_season else None
            liga_profesional = {
                "id": league["id"],
                "name": league["name"],
                "season": FREE_PLAN_SEASON,
                "api_current_season": api_season
            }
    
    return liga_profesional


def get_teams(league_id, season):
    """
    Obtiene los equipos de una liga para una temporada especifica.
    Endpoint: GET /teams
    """
    url = f"{BASE_URL}/teams"
    params = {
        "league": league_id,
        "season": season
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"ERROR: La API respondio con codigo {response.status_code}")
        return []
    
    data = response.json()
    
    if data.get("errors"):
        print(f"ERROR de API: {data['errors']}")
        return []
    
    return data["response"]


def display_teams(teams):
    """Muestra la lista de equipos de forma ordenada."""
    print("\n--- Equipos de la Liga ---")
    
    # Ordenar por nombre
    sorted_teams = sorted(teams, key=lambda x: x["team"]["name"])
    
    for i, team_data in enumerate(sorted_teams, 1):
        team = team_data["team"]
        print(f"  {i:2}. {team['name']} (ID: {team['id']})")
    
    return len(teams)


def main():
    """Funcion principal que ejecuta las verificaciones de la Fase 1."""
    print("=" * 50)
    print("ChatDT - Verificacion de Configuracion (Fase 1)")
    print("=" * 50)
    
    # Paso 1: Verificar API Key
    print("\n[1/4] Verificando API Key...")
    check_api_key()
    
    # Paso 2: Obtener ligas de Argentina
    print("\n[2/4] Consultando ligas de Argentina...")
    leagues = get_argentina_leagues()
    
    if not leagues:
        print("ERROR: No se encontraron ligas de Argentina")
        sys.exit(1)
    
    # Paso 3: Encontrar Liga Profesional
    print("\n[3/4] Buscando Liga Profesional...")
    liga = find_liga_profesional(leagues)
    
    if not liga:
        print("ADVERTENCIA: No se encontro la Liga Profesional automaticamente")
        print("Revisa la lista de ligas arriba y configura LEAGUE_ID manualmente en .env")
        sys.exit(1)
    
    print(f"\n>>> Liga encontrada: {liga['name']}")
    print(f"    ID: {liga['id']}")
    print(f"    Temporada en API: {liga['api_current_season']}")
    print(f"    Temporada a usar: {liga['season']} (limite del plan gratuito: 2021-2023)")
    
    # Paso 4: Obtener equipos
    print(f"\n[4/4] Obteniendo equipos de la temporada {liga['season']}...")
    teams = get_teams(liga["id"], liga["season"])
    
    if not teams:
        print("ERROR: No se pudieron obtener los equipos")
        sys.exit(1)
    
    total_teams = display_teams(teams)
    
    # Resumen final
    print("\n" + "=" * 50)
    print("RESULTADO DE LA VERIFICACION")
    print("=" * 50)
    print(f"Liga ID: {liga['id']} - Temporada: {liga['season']} - Equipos encontrados: {total_teams}")
    print("\nConfiguracion exitosa! Podes continuar con la Fase 2.")
    print("=" * 50)


if __name__ == "__main__":
    main()

