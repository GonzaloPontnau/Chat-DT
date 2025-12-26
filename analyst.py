"""
ChatDT - Fase 3: El Agente Sabermetrico (Logica de Negocio)

Este modulo transforma los datos crudos del Scout en metricas
propietarias, calculando el ChatDT Performance Score (CPS).

El CPS evalua el rendimiento real de un equipo mas alla del resultado,
respondiendo a la pregunta: "Quien jugo mejor?"

Componentes del CPS:
- Offensive Threat: Calidad y cantidad de ataques
- Control Efficiency: Dominio del balon y precision
- Friction Index: Impacto negativo de faltas y tarjetas

Uso:
    from analyst import AnalystAgent
    
    analyst = AnalystAgent()
    result = analyst.analyze_match("data/raw/match_full_971362.json")
    print(result['comparison'])
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pandas as pd


@dataclass
class CPSBreakdown:
    """Desglose del ChatDT Performance Score."""
    threat: float
    control: float
    friction: float
    total: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "threat": round(self.threat, 2),
            "control": round(self.control, 2),
            "friction": round(self.friction, 2),
            "total": round(self.total, 2)
        }


class AnalystAgent:
    """
    Agente Sabermetrico: Calcula el CPS Score de un partido.
    
    Transforma estadisticas crudas de API-FOOTBALL en un indice
    numerico que permite comparar objetivamente el rendimiento
    de ambos equipos.
    """
    
    # Pesos para el calculo del CPS
    # Ajustables segun preferencia tactica
    WEIGHTS = {
        # Offensive Threat
        "shots_on_goal": 3.0,
        "shots_inside_box": 2.0,
        "shots_outside_box": 0.5,
        "corner_kicks": 1.0,
        "offsides": -0.3,  # Penalizacion leve por ataques fallidos
        
        # Control Efficiency
        "possession": 0.4,
        "pass_accuracy": 0.5,
        "total_passes": 0.02,
        
        # Friction Index (negativo)
        "fouls": -0.5,
        "yellow_cards": -3.0,
        "red_cards": -10.0,
    }
    
    # Mapeo de nombres de estadisticas de la API a nombres internos
    STAT_MAPPING = {
        "Shots on Goal": "shots_on_goal",
        "Shots off Goal": "shots_off_goal",
        "Total Shots": "total_shots",
        "Blocked Shots": "blocked_shots",
        "Shots insidebox": "shots_inside_box",
        "Shots outsidebox": "shots_outside_box",
        "Fouls": "fouls",
        "Corner Kicks": "corner_kicks",
        "Offsides": "offsides",
        "Ball Possession": "possession",
        "Yellow Cards": "yellow_cards",
        "Red Cards": "red_cards",
        "Goalkeeper Saves": "goalkeeper_saves",
        "Total passes": "total_passes",
        "Passes accurate": "passes_accurate",
        "Passes %": "pass_accuracy",
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Inicializa el Analyst Agent.
        
        Args:
            weights: Pesos personalizados para el CPS (opcional)
        """
        if weights:
            self.WEIGHTS.update(weights)
    
    def load_match_data(self, filepath: str) -> Dict[str, Any]:
        """Carga datos de un partido desde JSON."""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"No se encontro: {filepath}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_statistics(self, stats_data: list) -> Dict[str, Dict[str, float]]:
        """
        Parsea y limpia estadisticas de la API.
        
        Convierte los datos crudos a un dict estructurado,
        manejando valores null y porcentajes.
        
        Args:
            stats_data: Lista de estadisticas por equipo de la API
            
        Returns:
            {"home": {...stats...}, "away": {...stats...}}
        """
        result = {"home": {}, "away": {}}
        
        if not stats_data or len(stats_data) < 2:
            print("[ANALYST] WARN: Estadisticas incompletas")
            return result
        
        for i, team_stats in enumerate(stats_data):
            key = "home" if i == 0 else "away"
            team_name = team_stats.get("team", {}).get("name", key)
            
            for stat in team_stats.get("statistics", []):
                stat_type = stat.get("type", "")
                value = stat.get("value")
                
                # Limpiar valor: null -> 0, porcentaje -> float
                clean_value = self._clean_stat_value(value)
                
                # Usar nombre interno si existe mapping
                internal_name = self.STAT_MAPPING.get(stat_type, stat_type.lower().replace(" ", "_"))
                result[key][internal_name] = clean_value
            
            result[key]["team_name"] = team_name
        
        return result
    
    def _clean_stat_value(self, value: Any) -> float:
        """
        Limpia un valor de estadistica.
        
        - None/null -> 0
        - "55%" -> 55.0
        - int/float -> float
        """
        if value is None:
            return 0.0
        
        if isinstance(value, str):
            # Remover % y convertir
            cleaned = value.replace("%", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return float(value)
    
    def calculate_cps(self, stats: Dict[str, float]) -> CPSBreakdown:
        """
        Calcula el ChatDT Performance Score para un equipo.
        
        Formula:
        CPS = Offensive_Threat + Control_Efficiency + Friction_Index
        
        Args:
            stats: Estadisticas limpias del equipo
            
        Returns:
            CPSBreakdown con desglose y total
        """
        # === OFFENSIVE THREAT ===
        # Mide la peligrosidad ofensiva
        threat = (
            stats.get("shots_on_goal", 0) * self.WEIGHTS["shots_on_goal"] +
            stats.get("shots_inside_box", 0) * self.WEIGHTS["shots_inside_box"] +
            stats.get("shots_outside_box", 0) * self.WEIGHTS["shots_outside_box"] +
            stats.get("corner_kicks", 0) * self.WEIGHTS["corner_kicks"] +
            stats.get("offsides", 0) * self.WEIGHTS["offsides"]
        )
        
        # === CONTROL EFFICIENCY ===
        # Mide el dominio del partido
        control = (
            stats.get("possession", 0) * self.WEIGHTS["possession"] +
            stats.get("pass_accuracy", 0) * self.WEIGHTS["pass_accuracy"] +
            stats.get("total_passes", 0) * self.WEIGHTS["total_passes"]
        )
        
        # === FRICTION INDEX ===
        # Impacto negativo de juego brusco
        friction = (
            stats.get("fouls", 0) * self.WEIGHTS["fouls"] +
            stats.get("yellow_cards", 0) * self.WEIGHTS["yellow_cards"] +
            stats.get("red_cards", 0) * self.WEIGHTS["red_cards"]
        )
        
        total = threat + control + friction
        
        return CPSBreakdown(
            threat=threat,
            control=control,
            friction=friction,
            total=total
        )
    
    def analyze_match(self, data_or_path) -> Dict[str, Any]:
        """
        Analiza un partido completo y determina quien jugo mejor.
        
        Args:
            data_or_path: Dict con datos del partido O ruta al JSON
            
        Returns:
            Dict con analisis completo:
            - match_info: Info basica del partido
            - stats: Estadisticas parseadas
            - home_cps/away_cps: CPS por equipo (para compatibilidad)
            - cps_scores: CPS por equipo
            - comparison: Quien jugo mejor y por cuanto
            - verdict: Texto explicativo
        """
        print(f"\n[ANALYST] Analizando partido...")
        
        # Cargar datos - puede ser dict o filepath
        if isinstance(data_or_path, dict):
            data = data_or_path
        else:
            data = self.load_match_data(data_or_path)
        
        # Extraer info del partido
        fixture = data.get("fixture", {})
        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})
        
        match_info = {
            "fixture_id": data.get("fixture_id"),
            "home_team": teams.get("home", {}).get("name", "Home"),
            "away_team": teams.get("away", {}).get("name", "Away"),
            "home_goals": goals.get("home", 0),
            "away_goals": goals.get("away", 0),
            "date": fixture.get("fixture", {}).get("date", "")[:10],
        }
        
        print(f"  Partido: {match_info['home_team']} {match_info['home_goals']}-{match_info['away_goals']} {match_info['away_team']}")
        
        # Parsear estadisticas
        stats = self.parse_statistics(data.get("statistics", []))
        
        # Calcular CPS para cada equipo
        home_cps = self.calculate_cps(stats.get("home", {}))
        away_cps = self.calculate_cps(stats.get("away", {}))
        
        print(f"\n  --- CPS Breakdown ---")
        print(f"  {match_info['home_team']}:")
        print(f"    Threat:   {home_cps.threat:+.1f}")
        print(f"    Control:  {home_cps.control:+.1f}")
        print(f"    Friction: {home_cps.friction:+.1f}")
        print(f"    TOTAL:    {home_cps.total:.1f}")
        
        print(f"\n  {match_info['away_team']}:")
        print(f"    Threat:   {away_cps.threat:+.1f}")
        print(f"    Control:  {away_cps.control:+.1f}")
        print(f"    Friction: {away_cps.friction:+.1f}")
        print(f"    TOTAL:    {away_cps.total:.1f}")
        
        # Comparacion
        diff = home_cps.total - away_cps.total
        
        if diff > 5:
            better_team = match_info['home_team']
            dominance = "claramente"
        elif diff > 2:
            better_team = match_info['home_team']
            dominance = "ligeramente"
        elif diff < -5:
            better_team = match_info['away_team']
            dominance = "claramente"
        elif diff < -2:
            better_team = match_info['away_team']
            dominance = "ligeramente"
        else:
            better_team = "Empate tecnico"
            dominance = ""
        
        comparison = {
            "home_score": round(home_cps.total, 2),
            "away_score": round(away_cps.total, 2),
            "difference": round(abs(diff), 2),
            "better_team": better_team,
            "dominance": dominance,
        }
        
        # Generar veredicto
        verdict = self._generate_verdict(match_info, comparison, home_cps, away_cps)
        
        print(f"\n  --- VEREDICTO ---")
        print(f"  {verdict}")
        
        # Formato compatible con app.py
        home_cps_dict = {
            "Threat": home_cps.threat,
            "Control": home_cps.control,
            "Friction": home_cps.friction,
            "TOTAL": home_cps.total,
        }
        away_cps_dict = {
            "Threat": away_cps.threat,
            "Control": away_cps.control,
            "Friction": away_cps.friction,
            "TOTAL": away_cps.total,
        }
        
        return {
            "match_info": match_info,
            "stats": {
                "home": stats.get("home", {}),
                "away": stats.get("away", {}),
            },
            "cps_scores": {
                "home": home_cps.to_dict(),
                "away": away_cps.to_dict(),
            },
            # Para compatibilidad con app.py
            "home_cps": home_cps_dict,
            "away_cps": away_cps_dict,
            "comparison": comparison,
            "verdict": verdict,
        }
    
    def _generate_verdict(
        self, 
        match_info: Dict, 
        comparison: Dict,
        home_cps: CPSBreakdown,
        away_cps: CPSBreakdown
    ) -> str:
        """Genera un veredicto textual del analisis."""
        home = match_info['home_team']
        away = match_info['away_team']
        home_goals = match_info['home_goals']
        away_goals = match_info['away_goals']
        
        # Determinar ganador real del partido
        if home_goals > away_goals:
            winner = home
            winner_cps = home_cps.total
        elif away_goals > home_goals:
            winner = away
            winner_cps = away_cps.total
        else:
            winner = None
            winner_cps = 0
        
        better = comparison['better_team']
        diff = comparison['difference']
        
        # Obtener CPS del mejor equipo segun metricas
        better_cps = home_cps.total if better == home else away_cps.total
        
        # Caso 1: El mejor equipo gano
        if winner and winner == better:
            return (
                f"{winner} gano y merecio el triunfo. "
                f"Su CPS de {winner_cps:.1f} fue superior por {diff:.1f} puntos."
            )
        
        # Caso 2: Empate tecnico pero hubo ganador
        if winner and better == "Empate tecnico":
            return (
                f"Partido parejo. {winner} se llevo los 3 puntos pero "
                f"el rendimiento fue muy similar (diferencia de solo {diff:.1f} puntos)."
            )
        
        # Caso 3: El mejor equipo perdio
        if winner and winner != better and better != "Empate tecnico":
            return (
                f"Resultado injusto! {better} fue el mejor equipo con un CPS de {better_cps:.1f}, "
                f"superior por {diff:.1f} puntos, pero {winner} se llevo la victoria. "
                f"El futbol a veces no premia al mejor."
            )
        
        # Caso 4: Empate real
        if not winner:
            if better == "Empate tecnico":
                return f"Empate justo. Ambos equipos rindieron de manera similar."
            else:
                return (
                    f"Empate con sabor a poco para {better}, "
                    f"que fue superior por {diff:.1f} puntos de CPS."
                )
        
        return "Analisis completado."
    
    def to_dataframe(self, analysis: Dict[str, Any]) -> pd.DataFrame:
        """
        Convierte el analisis a un DataFrame para visualizacion.
        
        Returns:
            DataFrame con metricas comparativas
        """
        home = analysis['match_info']['home_team']
        away = analysis['match_info']['away_team']
        
        data = {
            "Metrica": [],
            home: [],
            away: [],
        }
        
        # Agregar estadisticas principales
        home_stats = analysis['stats']['home']
        away_stats = analysis['stats']['away']
        
        metrics = [
            ("Shots on Goal", "shots_on_goal"),
            ("Shots Inside Box", "shots_inside_box"),
            ("Total Shots", "total_shots"),
            ("Possession %", "possession"),
            ("Pass Accuracy %", "pass_accuracy"),
            ("Corner Kicks", "corner_kicks"),
            ("Fouls", "fouls"),
            ("Yellow Cards", "yellow_cards"),
        ]
        
        for label, key in metrics:
            data["Metrica"].append(label)
            data[home].append(home_stats.get(key, 0))
            data[away].append(away_stats.get(key, 0))
        
        # Agregar CPS
        data["Metrica"].append("--- CPS ---")
        data[home].append("")
        data[away].append("")
        
        for label, key in [("Threat", "threat"), ("Control", "control"), ("Friction", "friction"), ("TOTAL CPS", "total")]:
            data["Metrica"].append(label)
            data[home].append(analysis['cps_scores']['home'][key])
            data[away].append(analysis['cps_scores']['away'][key])
        
        return pd.DataFrame(data)


def main():
    """Script de prueba para el Analyst Agent."""
    print("=" * 70)
    print("ChatDT - Analyst Agent Test (Fase 3)")
    print("=" * 70)
    
    analyst = AnalystAgent()
    
    # Buscar archivos de partidos en data/raw
    raw_dir = Path("data/raw")
    match_files = list(raw_dir.glob("match_full_*.json"))
    
    if not match_files:
        print("\n[ERROR] No hay archivos de partidos en data/raw/")
        print("Ejecuta primero: python scout.py")
        return
    
    # Analizar el primer partido encontrado
    match_file = match_files[0]
    print(f"\nAnalizando: {match_file}")
    
    result = analyst.analyze_match(str(match_file))
    
    # Mostrar DataFrame comparativo
    print("\n" + "=" * 70)
    print("TABLA COMPARATIVA")
    print("=" * 70)
    df = analyst.to_dataframe(result)
    print(df.to_string(index=False))
    
    # Guardar resultado
    output_path = Path("data/processed") / f"analysis_{result['match_info']['fixture_id']}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVE] Analisis guardado en: {output_path}")
    
    print("\n" + "=" * 70)
    print("FASE 3 COMPLETADA")
    print("=" * 70)
    print(f"CPS {result['match_info']['home_team']}: {result['comparison']['home_score']}")
    print(f"CPS {result['match_info']['away_team']}: {result['comparison']['away_score']}")
    print(f"\nVeredicto: {result['verdict']}")


if __name__ == "__main__":
    main()

