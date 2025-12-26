"""
ChatDT - El Agente Scout (Data Ingestion Layer)

IMPORTANTE: Este modulo soporta dos fuentes de datos:

1. SOCCERDATA (FBref) - Para ligas europeas con metricas avanzadas (xG, PSxG, SCA)
   Ligas soportadas: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, World Cup

2. API-FOOTBALL - Para la Liga Argentina (y otras ligas no soportadas por FBref)
   Requiere API key de https://dashboard.api-football.com

Uso:
    # Para ligas europeas (FBref con xG)
    scout = ScoutAgent(source="fbref", league="ENG-Premier League", season="2024")
    
    # Para Liga Argentina (API-FOOTBALL)
    scout = ScoutAgent(source="api-football", league_id=128, season=2023)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import warnings

import pandas as pd
from dotenv import load_dotenv
import requests

# Cargar variables de entorno
load_dotenv()

# Suprimir warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Directorios para datos
DATA_DIR = Path("data")
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
SOCCERDATA_DIR = DATA_DIR / "soccerdata_cache"

# API-FOOTBALL config
API_KEY = os.getenv("API_FOOTBALL_KEY")
API_BASE_URL = "https://v3.football.api-sports.io"
API_HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

# Plan gratuito API-FOOTBALL: temporadas 2021-2023
FREE_PLAN_SEASON = 2023


class ScoutAgent:
    """
    Agente Scout: Ingesta de datos desde multiples fuentes.
    
    Soporta:
    - FBref (via soccerdata): Metricas avanzadas para ligas europeas
    - API-FOOTBALL: Datos para Liga Argentina y otras ligas
    
    Attributes:
        source: "fbref" o "api-football"
        league: Codigo de liga
        season: Temporada
    """
    
    # Ligas soportadas por FBref
    FBREF_LEAGUES = [
        "ENG-Premier League",
        "ESP-La Liga", 
        "ITA-Serie A",
        "GER-Bundesliga",
        "FRA-Ligue 1",
        "Big 5 European Leagues Combined",
        "INT-World Cup",
        "INT-Women's World Cup"
    ]
    
    def __init__(
        self,
        source: str = "api-football",
        league: Optional[str] = None,
        league_id: Optional[int] = 128,
        season: Union[str, int] = FREE_PLAN_SEASON
    ):
        """
        Inicializa el Scout Agent.
        
        Args:
            source: "fbref" o "api-football"
            league: Codigo de liga para FBref (ej: "ENG-Premier League")
            league_id: ID de liga para API-FOOTBALL (ej: 128 = Argentina)
            season: Temporada (año)
        """
        self.source = source.lower()
        self.league = league
        self.league_id = league_id
        self.season = int(season) if isinstance(season, str) else season
        
        # Crear directorios
        self._setup_directories()
        
        print(f"[SCOUT] Inicializando...")
        print(f"  Fuente: {self.source.upper()}")
        
        if self.source == "fbref":
            self._init_fbref()
        else:
            self._init_api_football()
    
    def _setup_directories(self):
        """Crea estructura de directorios."""
        for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, SOCCERDATA_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _init_fbref(self):
        """Inicializa cliente FBref."""
        if self.league not in self.FBREF_LEAGUES:
            print(f"  [ERROR] Liga '{self.league}' no soportada por FBref")
            print(f"  Ligas disponibles: {self.FBREF_LEAGUES}")
            self.fbref = None
            return
        
        try:
            import soccerdata as sd
            self.fbref = sd.FBref(
                leagues=self.league,
                seasons=str(self.season),
                data_dir=SOCCERDATA_DIR
            )
            print(f"  [OK] FBref: {self.league} - {self.season}")
        except Exception as e:
            print(f"  [ERROR] FBref: {e}")
            self.fbref = None
    
    def _init_api_football(self):
        """Inicializa cliente API-FOOTBALL."""
        self.fbref = None
        
        if not API_KEY:
            print("  [ERROR] API_FOOTBALL_KEY no configurada en .env")
            return
        
        print(f"  [OK] API-FOOTBALL: Liga ID {self.league_id} - Temporada {self.season}")
        
        # Verificar limites del plan gratuito
        if self.season > 2023:
            print(f"  [WARN] Plan gratuito solo permite 2021-2023. Usando {FREE_PLAN_SEASON}")
            self.season = FREE_PLAN_SEASON
    
    # =========================================================================
    # API-FOOTBALL METHODS
    # =========================================================================
    
    def _api_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Realiza request a API-FOOTBALL."""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=API_HEADERS, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("errors") and len(data["errors"]) > 0:
                print(f"  [API ERROR] {data['errors']}")
                return None
            
            remaining = response.headers.get("x-ratelimit-requests-remaining", "?")
            print(f"  [API] Requests restantes: {remaining}")
            
            return data
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None
    
    def _load_cache(self, name: str) -> Optional[dict]:
        """Carga datos desde cache."""
        cache_path = DATA_RAW_DIR / f"{name}.json"
        if cache_path.exists():
            print(f"  [CACHE] Cargando {cache_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_cache(self, name: str, data: Any):
        """Guarda datos en cache."""
        cache_path = DATA_RAW_DIR / f"{name}.json"
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  [CACHE] Guardado en {cache_path}")
    
    def get_last_matches(self, team_id: int, limit: int = 10, use_cache: bool = True) -> List[dict]:
        """
        Obtiene ultimos partidos de un equipo (API-FOOTBALL).
        
        Args:
            team_id: ID del equipo (ej: 451 = Boca Juniors)
            limit: Cantidad de partidos
            use_cache: Usar cache local
            
        Returns:
            Lista de partidos
        """
        print(f"\n[SCOUT] Buscando ultimos {limit} partidos del equipo {team_id}...")
        
        cache_key = f"matches_team_{team_id}_s{self.season}"
        
        if use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                return cached[:limit]
        
        # NOTA: El plan gratuito no soporta el parametro "last"
        # Usamos solo los filtros basicos
        data = self._api_request("/fixtures", {
            "team": team_id,
            "league": self.league_id,
            "season": self.season,
            "status": "FT"
        })
        
        if not data or not data.get("response"):
            return []
        
        matches = data["response"]
        self._save_cache(cache_key, matches)
        
        print(f"  Partidos encontrados: {len(matches)}")
        for m in matches[:5]:
            f = m["fixture"]
            t = m["teams"]
            g = m["goals"]
            print(f"    {f['date'][:10]}: {t['home']['name']} {g['home']}-{g['away']} {t['away']['name']}")
        
        return matches
    
    def get_match_stats(self, fixture_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """
        Obtiene estadisticas completas de un partido (API-FOOTBALL).
        
        Args:
            fixture_id: ID del partido
            use_cache: Usar cache local
            
        Returns:
            Dict con fixture, statistics, events, predictions
        """
        print(f"\n[SCOUT] Obteniendo datos del partido {fixture_id}...")
        
        cache_key = f"match_full_{fixture_id}"
        
        if use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                return cached
        
        match_data = {
            "fixture_id": fixture_id,
            "fetched_at": datetime.now().isoformat(),
            "fixture": None,
            "statistics": None,
            "events": None,
            "lineups": None,
            "predictions": None
        }
        
        # 1. Info del partido
        print("  [1/5] Fixture info...")
        data = self._api_request("/fixtures", {"id": fixture_id})
        if data and data.get("response"):
            match_data["fixture"] = data["response"][0]
        
        # 2. Estadisticas
        print("  [2/5] Statistics...")
        data = self._api_request("/fixtures/statistics", {"fixture": fixture_id})
        if data and data.get("response"):
            match_data["statistics"] = data["response"]
        
        # 3. Eventos
        print("  [3/5] Events...")
        data = self._api_request("/fixtures/events", {"fixture": fixture_id})
        if data and data.get("response"):
            match_data["events"] = data["response"]
        
        # 4. Lineups
        print("  [4/5] Lineups...")
        data = self._api_request("/fixtures/lineups", {"fixture": fixture_id})
        if data and data.get("response"):
            match_data["lineups"] = data["response"]
        
        # 5. Predictions
        print("  [5/5] Predictions...")
        data = self._api_request("/predictions", {"fixture": fixture_id})
        if data and data.get("response"):
            match_data["predictions"] = data["response"]
        
        self._save_cache(cache_key, match_data)
        
        # Resumen
        if match_data["fixture"]:
            f = match_data["fixture"]
            t = f["teams"]
            g = f["goals"]
            print(f"\n  Partido: {t['home']['name']} {g['home']}-{g['away']} {t['away']['name']}")
            print(f"  Statistics: {'OK' if match_data['statistics'] else 'N/A'}")
            print(f"  Events: {len(match_data['events']) if match_data['events'] else 0}")
            print(f"  Lineups: {'OK' if match_data['lineups'] else 'N/A'}")
        
        return match_data
    
    def get_head_to_head(self, team1_id: int, team2_id: int, use_cache: bool = True) -> List[dict]:
        """
        Busca enfrentamientos directos entre dos equipos.
        
        Args:
            team1_id: ID del primer equipo
            team2_id: ID del segundo equipo
            
        Returns:
            Lista de partidos entre ambos equipos
        """
        print(f"\n[SCOUT] Buscando {team1_id} vs {team2_id}...")
        
        cache_key = f"h2h_{team1_id}_vs_{team2_id}"
        
        if use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                return cached
        
        data = self._api_request("/fixtures", {
            "h2h": f"{team1_id}-{team2_id}",
            "league": self.league_id,
            "season": self.season,
            "status": "FT"
        })
        
        if not data or not data.get("response"):
            return []
        
        matches = data["response"]
        self._save_cache(cache_key, matches)
        
        print(f"  Enfrentamientos: {len(matches)}")
        for m in matches:
            f = m["fixture"]
            t = m["teams"]
            g = m["goals"]
            print(f"    {f['date'][:10]}: {t['home']['name']} {g['home']}-{g['away']} {t['away']['name']}")
        
        return matches
    
    # =========================================================================
    # FBREF METHODS (para ligas europeas)
    # =========================================================================
    
    def get_schedule_fbref(self) -> pd.DataFrame:
        """Obtiene calendario desde FBref."""
        if not self.fbref:
            print("  [ERROR] FBref no disponible")
            return pd.DataFrame()
        
        print("\n[SCOUT] Obteniendo calendario (FBref)...")
        try:
            schedule = self.fbref.read_schedule()
            self._save_dataframe(schedule, "schedule_fbref")
            return schedule
        except Exception as e:
            print(f"  [ERROR] {e}")
            return pd.DataFrame()
    
    def get_shooting_stats_fbref(self, stat_type: str = "team") -> pd.DataFrame:
        """
        Obtiene estadisticas de tiros con xG (FBref).
        
        Columnas incluidas:
        - Gls, Sh, SoT, SoT%
        - xG, npxG, G-xG (diferencia goles vs xG)
        """
        if not self.fbref:
            return pd.DataFrame()
        
        print(f"\n[SCOUT] Obteniendo shooting stats (FBref)...")
        try:
            if stat_type == "player":
                stats = self.fbref.read_player_season_stats(stat_type="shooting")
            else:
                stats = self.fbref.read_team_season_stats(stat_type="shooting")
            
            self._save_dataframe(stats, f"shooting_{stat_type}_fbref")
            print(f"  [OK] {len(stats)} registros")
            return stats
        except Exception as e:
            print(f"  [ERROR] {e}")
            return pd.DataFrame()
    
    def get_passing_stats_fbref(self, stat_type: str = "team") -> pd.DataFrame:
        """Obtiene estadisticas de pases (FBref)."""
        if not self.fbref:
            return pd.DataFrame()
        
        print(f"\n[SCOUT] Obteniendo passing stats (FBref)...")
        try:
            if stat_type == "player":
                stats = self.fbref.read_player_season_stats(stat_type="passing")
            else:
                stats = self.fbref.read_team_season_stats(stat_type="passing")
            
            self._save_dataframe(stats, f"passing_{stat_type}_fbref")
            return stats
        except Exception as e:
            print(f"  [ERROR] {e}")
            return pd.DataFrame()
    
    def get_gca_stats_fbref(self, stat_type: str = "team") -> pd.DataFrame:
        """
        Obtiene estadisticas de acciones creativas (FBref).
        
        Columnas incluidas:
        - SCA (Shot-Creating Actions)
        - GCA (Goal-Creating Actions)
        """
        if not self.fbref:
            return pd.DataFrame()
        
        print(f"\n[SCOUT] Obteniendo GCA stats (FBref)...")
        try:
            if stat_type == "player":
                stats = self.fbref.read_player_season_stats(stat_type="gca")
            else:
                stats = self.fbref.read_team_season_stats(stat_type="gca")
            
            self._save_dataframe(stats, f"gca_{stat_type}_fbref")
            return stats
        except Exception as e:
            print(f"  [ERROR] {e}")
            return pd.DataFrame()
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _save_dataframe(self, df: pd.DataFrame, name: str):
        """Guarda DataFrame como CSV y JSON."""
        if df.empty:
            return
        
        csv_path = DATA_PROCESSED_DIR / f"{name}_{self.season}.csv"
        df.to_csv(csv_path)
        
        json_path = DATA_RAW_DIR / f"{name}_{self.season}.json"
        df.to_json(json_path, orient="records", indent=2)
        
        print(f"  [SAVE] {csv_path}")
    
    def parse_statistics(self, stats_data: List[dict]) -> Dict[str, Dict[str, Any]]:
        """
        Parsea estadisticas de API-FOOTBALL a dict mas usable.
        
        Returns:
            {
                "home": {"Shots on Goal": 5, "Ball Possession": "55%", ...},
                "away": {"Shots on Goal": 3, "Ball Possession": "45%", ...}
            }
        """
        result = {"home": {}, "away": {}}
        
        if not stats_data or len(stats_data) < 2:
            return result
        
        for i, team_stats in enumerate(stats_data):
            key = "home" if i == 0 else "away"
            for stat in team_stats.get("statistics", []):
                stat_type = stat.get("type", "")
                value = stat.get("value")
                # Convertir porcentajes a numeros
                if isinstance(value, str) and "%" in value:
                    try:
                        value = float(value.replace("%", ""))
                    except:
                        pass
                result[key][stat_type] = value if value is not None else 0
        
        return result


def main():
    """Script de prueba."""
    print("=" * 70)
    print("ChatDT - Scout Agent Test")
    print("=" * 70)
    
    # IDs de equipos argentinos
    BOCA = 451
    RIVER = 435
    
    # =========================================================================
    # OPCION 1: Liga Argentina con API-FOOTBALL
    # =========================================================================
    print("\n" + "=" * 70)
    print("OPCION 1: Liga Argentina (API-FOOTBALL)")
    print("=" * 70)
    
    scout_arg = ScoutAgent(
        source="api-football",
        league_id=128,  # Liga Profesional Argentina
        season=2023
    )
    
    # Buscar ultimos partidos de Boca
    boca_matches = scout_arg.get_last_matches(BOCA, limit=5)
    
    if boca_matches:
        # Descargar datos del primer partido
        fixture_id = boca_matches[0]["fixture"]["id"]
        match_data = scout_arg.get_match_stats(fixture_id)
        
        # Mostrar estadisticas parseadas
        if match_data.get("statistics"):
            print("\n--- Estadisticas Parseadas ---")
            parsed = scout_arg.parse_statistics(match_data["statistics"])
            for team, stats in parsed.items():
                print(f"\n{team.upper()}:")
                for k, v in list(stats.items())[:8]:
                    print(f"  {k}: {v}")
    
    # =========================================================================
    # OPCION 2: Premier League con FBref (xG disponible)
    # =========================================================================
    print("\n" + "=" * 70)
    print("OPCION 2: Premier League (FBref - xG stats)")
    print("=" * 70)
    
    scout_epl = ScoutAgent(
        source="fbref",
        league="ENG-Premier League",
        season=2024
    )
    
    # Solo si FBref esta disponible
    if scout_epl.fbref:
        shooting = scout_epl.get_shooting_stats_fbref("team")
        if not shooting.empty:
            print("\nColumnas de Shooting Stats:")
            print(list(shooting.columns)[:15])
            print("\nPrimeras filas:")
            print(shooting.head())
    
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("""
    FUENTES DE DATOS:
    
    1. API-FOOTBALL (Liga Argentina):
       - Shots on Goal, Ball Possession, Passes, Fouls, etc.
       - Sin xG (Expected Goals)
       - Incluye lineups con grid positions
       
    2. FBref (Ligas Europeas):
       - xG, npxG, PSxG
       - SCA, GCA (acciones creativas)
       - Stats avanzadas de pases
       
    Para el CPS Score de Liga Argentina, usaremos las metricas
    disponibles en API-FOOTBALL y calcularemos nuestro propio
    modelo de "Expected Performance".
    """)


if __name__ == "__main__":
    main()
