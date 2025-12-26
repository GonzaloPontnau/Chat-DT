"""
ChatDT: The Agentic Football Analyst
=====================================

Sistema Multi-Agente que analiza partidos de futbol argentino usando LangGraph.
Genera metricas de rendimiento (CPS Score), visualizaciones tacticas y 
cronicas periodisticas automaticas.

Pipeline: Scout -> Analyst -> Visualizer -> Writer

Uso:
    python main.py                    # Analiza fixture por defecto
    python main.py --fixture 971362   # Analiza fixture especifico
    python main.py --team 451         # Analiza ultimo partido del equipo

Requiere en .env:
    - API_FOOTBALL_KEY (datos de partidos)
    - GROQ_API_KEY o GOOGLE_API_KEY (LLM gratis)
"""

import os
import json
import argparse
from pathlib import Path
from typing import TypedDict, Annotated, Optional, List
from datetime import datetime

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage

# Configuracion de LLM
# Opciones: "groq" (GRATIS), "gemini" (gratis), "openai" (pago)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Modelos por proveedor (actualizados Dic 2024)
LLM_MODELS = {
    "gemini": "gemini-2.0-flash-lite",  # GRATIS - 30 req/min, 1500 req/dia
    "gemini-pro": "gemini-1.5-pro",     # GRATIS - 2 req/min, 50 req/dia  
    "groq": "llama-3.3-70b-versatile",  # GRATIS - 30 req/min (modelo actual)
    "openai": "gpt-4o",                 # PAGO
}

# Importar agentes locales
from scout import ScoutAgent
from analyst import AnalystAgent
from visualizer import VisualizerAgent

# Cargar variables de entorno
load_dotenv()

# Directorios
DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")
REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    """Estado compartido entre todos los nodos del grafo."""
    # Input
    fixture_id: Optional[int]
    team_id: Optional[int]
    
    # Scout output
    raw_data: Optional[dict]
    match_info: Optional[dict]
    
    # Analyst output
    analysis: Optional[dict]
    cps_scores: Optional[dict]
    
    # Visualizer output
    visualization_path: Optional[str]
    
    # Writer output
    report_markdown: Optional[str]
    report_path: Optional[str]
    
    # Metadata
    errors: List[str]
    status: str


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

def node_scout(state: AgentState) -> AgentState:
    """
    Nodo Scout: Obtiene datos del partido desde API o cache.
    
    Input: fixture_id o team_id
    Output: raw_data, match_info
    """
    print("\n" + "=" * 60)
    print("NODE: SCOUT - Ingesta de Datos")
    print("=" * 60)
    
    errors = state.get("errors", [])
    
    scout = ScoutAgent(source="api-football", league_id=128, season=2023)
    
    fixture_id = state.get("fixture_id")
    team_id = state.get("team_id")
    
    # Si tenemos fixture_id, buscar directamente
    if fixture_id:
        # Verificar si ya existe en cache
        cache_path = DATA_RAW / f"match_full_{fixture_id}.json"
        if cache_path.exists():
            print(f"  [CACHE] Cargando {cache_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        else:
            raw_data = scout.get_match_stats(fixture_id)
    
    # Si tenemos team_id, buscar ultimo partido
    elif team_id:
        matches = scout.get_last_matches(team_id, limit=1)
        if matches:
            fixture_id = matches[0]["fixture"]["id"]
            raw_data = scout.get_match_stats(fixture_id)
        else:
            errors.append(f"No se encontraron partidos para equipo {team_id}")
            return {**state, "errors": errors, "status": "error"}
    
    else:
        # Buscar cualquier archivo de partido en cache
        cache_files = list(DATA_RAW.glob("match_full_*.json"))
        if cache_files:
            print(f"  [CACHE] Usando archivo existente: {cache_files[0]}")
            with open(cache_files[0], 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            fixture_id = raw_data.get("fixture_id")
        else:
            errors.append("No se especifico fixture_id ni team_id, y no hay cache")
            return {**state, "errors": errors, "status": "error"}
    
    # Extraer match_info
    fixture = raw_data.get("fixture", {})
    teams = fixture.get("teams", {})
    goals = fixture.get("goals", {})
    
    match_info = {
        "fixture_id": fixture_id,
        "home_team": teams.get("home", {}).get("name", "Home"),
        "away_team": teams.get("away", {}).get("name", "Away"),
        "home_goals": goals.get("home", 0),
        "away_goals": goals.get("away", 0),
        "date": fixture.get("fixture", {}).get("date", "")[:10],
        "venue": fixture.get("fixture", {}).get("venue", {}).get("name", ""),
    }
    
    print(f"\n  Partido encontrado: {match_info['home_team']} {match_info['home_goals']}-{match_info['away_goals']} {match_info['away_team']}")
    
    return {
        **state,
        "fixture_id": fixture_id,
        "raw_data": raw_data,
        "match_info": match_info,
        "status": "scout_complete"
    }


def node_analyst(state: AgentState) -> AgentState:
    """
    Nodo Analyst: Calcula el CPS Score del partido.
    
    Input: raw_data
    Output: analysis, cps_scores
    """
    print("\n" + "=" * 60)
    print("NODE: ANALYST - Calculo de CPS Score")
    print("=" * 60)
    
    errors = state.get("errors", [])
    raw_data = state.get("raw_data")
    fixture_id = state.get("fixture_id")
    
    if not raw_data:
        errors.append("No hay raw_data para analizar")
        return {**state, "errors": errors, "status": "error"}
    
    # Guardar temporalmente para el analyst
    temp_path = DATA_RAW / f"match_full_{fixture_id}.json"
    
    analyst = AnalystAgent()
    analysis = analyst.analyze_match(str(temp_path))
    
    return {
        **state,
        "analysis": analysis,
        "cps_scores": analysis.get("cps_scores"),
        "status": "analyst_complete"
    }


def node_visualizer(state: AgentState) -> AgentState:
    """
    Nodo Visualizer: Genera graficos del partido.
    
    Input: raw_data, analysis
    Output: visualization_path
    """
    print("\n" + "=" * 60)
    print("NODE: VISUALIZER - Generacion de Graficos")
    print("=" * 60)
    
    fixture_id = state.get("fixture_id")
    match_path = DATA_RAW / f"match_full_{fixture_id}.json"
    
    viz = VisualizerAgent(style="dark")
    output_path = viz.create_match_report(str(match_path))
    
    return {
        **state,
        "visualization_path": output_path,
        "status": "visualizer_complete"
    }


def node_writer(state: AgentState) -> AgentState:
    """
    Nodo Writer: Genera cronica periodistica con GPT-4o.
    
    Input: match_info, analysis, cps_scores
    Output: report_markdown, report_path
    """
    print("\n" + "=" * 60)
    print("NODE: WRITER - Generacion de Cronica (LLM)")
    print("=" * 60)
    
    errors = state.get("errors", [])
    
    # Verificar API key segun proveedor
    provider = LLM_PROVIDER.lower()
    
    api_keys = {
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "gemini-pro": os.getenv("GOOGLE_API_KEY"),
        "groq": os.getenv("GROQ_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
    }
    
    has_key = api_keys.get(provider)
    
    if not has_key:
        key_name = "GOOGLE_API_KEY" if "gemini" in provider else f"{provider.upper()}_API_KEY"
        print(f"  [WARN] {key_name} no configurada, generando reporte basico")
        print(f"\n  === OPCIONES GRATUITAS ===")
        print(f"  1. Google Gemini (RECOMENDADO):")
        print(f"     - Ve a: https://aistudio.google.com/apikey")
        print(f"     - Crea API key gratis (solo cuenta Google)")
        print(f"     - En .env: GOOGLE_API_KEY=tu_key")
        print(f"\n  2. Groq:")
        print(f"     - Ve a: https://console.groq.com/keys")
        print(f"     - En .env: LLM_PROVIDER=groq")
        print(f"     - En .env: GROQ_API_KEY=tu_key")
        report = generate_basic_report(state)
    else:
        report = generate_llm_report(state)
    
    # Guardar reporte
    fixture_id = state.get("fixture_id")
    report_path = REPORTS_DIR / f"report_{fixture_id}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n  [SAVE] Reporte guardado: {report_path}")
    
    return {
        **state,
        "report_markdown": report,
        "report_path": str(report_path),
        "status": "complete"
    }


def get_llm_client():
    """
    Obtiene el cliente LLM segun el proveedor configurado.
    
    Proveedores soportados (todos con tier GRATIS):
    - gemini: Google Gemini 1.5 Flash (15 req/min, 1500 req/dia) - RECOMENDADO
    - groq: Llama 3.1 70B (30 req/min, gratis)
    - openai: GPT-4o (pago)
    """
    provider = LLM_PROVIDER.lower()
    
    # OPCION 1: Google Gemini (GRATIS - RECOMENDADO)
    if provider in ["gemini", "gemini-pro"]:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        model = LLM_MODELS.get(provider, "gemini-1.5-flash")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=1500
        )
    
    # OPCION 2: Groq (GRATIS)
    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=LLM_MODELS["groq"],
            openai_api_key=api_key,
            openai_api_base="https://api.groq.com/openai/v1",
            temperature=0.7,
            max_tokens=1500
        )
    
    # OPCION 3: OpenAI (PAGO)
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=LLM_MODELS["openai"],
            temperature=0.7,
            max_tokens=1500
        )


def generate_llm_report(state: AgentState) -> str:
    """Genera cronica periodistica usando el LLM configurado."""
    print(f"  Conectando con {LLM_PROVIDER.upper()} ({LLM_MODELS.get(LLM_PROVIDER, 'default')})...")
    
    match_info = state.get("match_info", {})
    analysis = state.get("analysis", {})
    cps_scores = state.get("cps_scores", {})
    raw_data = state.get("raw_data", {})
    
    # Extraer eventos del partido
    events = raw_data.get("events", [])
    goals = [e for e in events if e.get("type") == "Goal"]
    cards = [e for e in events if e.get("type") == "Card"]
    
    # Construir contexto para el LLM
    context = f"""
DATOS DEL PARTIDO:
- {match_info.get('home_team')} {match_info.get('home_goals')} - {match_info.get('away_goals')} {match_info.get('away_team')}
- Fecha: {match_info.get('date')}
- Estadio: {match_info.get('venue')}

ESTADISTICAS (CPS - ChatDT Performance Score):
{match_info.get('home_team')}:
  - Threat (Peligro ofensivo): {cps_scores.get('home', {}).get('threat', 0):.1f}
  - Control (Dominio): {cps_scores.get('home', {}).get('control', 0):.1f}
  - Friction (Impacto negativo): {cps_scores.get('home', {}).get('friction', 0):.1f}
  - TOTAL CPS: {cps_scores.get('home', {}).get('total', 0):.1f}

{match_info.get('away_team')}:
  - Threat: {cps_scores.get('away', {}).get('threat', 0):.1f}
  - Control: {cps_scores.get('away', {}).get('control', 0):.1f}
  - Friction: {cps_scores.get('away', {}).get('friction', 0):.1f}
  - TOTAL CPS: {cps_scores.get('away', {}).get('total', 0):.1f}

GOLES:
"""
    for goal in goals:
        player = goal.get("player", {}).get("name", "Desconocido")
        team = goal.get("team", {}).get("name", "")
        minute = goal.get("time", {}).get("elapsed", 0)
        context += f"  - {player} ({team}) - Minuto {minute}\n"
    
    context += f"\nTARJETAS AMARILLAS: {len([c for c in cards if c.get('detail') == 'Yellow Card'])}"
    context += f"\nTARJETAS ROJAS: {len([c for c in cards if c.get('detail') == 'Red Card'])}"
    context += f"\n\nVEREDICTO DEL SISTEMA: {analysis.get('verdict', '')}"
    
    # Crear prompt
    system_prompt = """Eres un periodista deportivo argentino experto en futbol, similar a Juan Pablo Varsky.
Tu tarea es escribir una cronica del partido en formato Markdown.

ESTILO:
- Usa lenguaje argentino (vos, che, etc.)
- Se apasionado pero objetivo
- Cita las estadisticas del CPS Score para justificar tus conclusiones
- Menciona a los goleadores y momentos clave
- El titulo debe ser llamativo y reflejar la narrativa del partido

FORMATO:
- Titulo con # 
- Subtitulos con ##
- Negrita para nombres de equipos y jugadores clave
- Incluye una seccion "Por los numeros" citando el CPS Score
- Concluye con un veredicto final

Escribe entre 400-600 palabras."""

    user_prompt = f"Escribe la cronica de este partido:\n\n{context}"
    
    # Obtener cliente LLM
    llm = get_llm_client()
    
    if not llm:
        print(f"  [ERROR] No hay API key configurada para {LLM_PROVIDER}")
        return generate_basic_report(state)
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        report = response.content
        
        print(f"  [OK] Cronica generada por {LLM_PROVIDER.upper()}")
        
    except Exception as e:
        print(f"  [ERROR] {LLM_PROVIDER}: {e}")
        report = generate_basic_report(state)
    
    return report


def generate_basic_report(state: AgentState) -> str:
    """Genera un reporte basico sin LLM."""
    match_info = state.get("match_info", {})
    analysis = state.get("analysis", {})
    cps_scores = state.get("cps_scores", {})
    viz_path = state.get("visualization_path", "")
    
    home = match_info.get('home_team', 'Home')
    away = match_info.get('away_team', 'Away')
    
    report = f"""# {home} {match_info.get('home_goals')}-{match_info.get('away_goals')} {away}

**Fecha:** {match_info.get('date')}  
**Estadio:** {match_info.get('venue')}

---

## Analisis ChatDT

### CPS Score (ChatDT Performance Score)

| Metrica | {home} | {away} |
|---------|--------|--------|
| Threat | {cps_scores.get('home', {}).get('threat', 0):.1f} | {cps_scores.get('away', {}).get('threat', 0):.1f} |
| Control | {cps_scores.get('home', {}).get('control', 0):.1f} | {cps_scores.get('away', {}).get('control', 0):.1f} |
| Friction | {cps_scores.get('home', {}).get('friction', 0):.1f} | {cps_scores.get('away', {}).get('friction', 0):.1f} |
| **TOTAL** | **{cps_scores.get('home', {}).get('total', 0):.1f}** | **{cps_scores.get('away', {}).get('total', 0):.1f}** |

---

## Veredicto

{analysis.get('verdict', 'Analisis completado.')}

---

## Visualizacion

![Match Analysis]({viz_path})

---

*Generado por ChatDT - The Agentic Football Analyst*  
*{datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    return report


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph() -> StateGraph:
    """Construye el grafo de LangGraph."""
    
    # Crear grafo
    graph = StateGraph(AgentState)
    
    # Agregar nodos
    graph.add_node("scout", node_scout)
    graph.add_node("analyst", node_analyst)
    graph.add_node("visualizer", node_visualizer)
    graph.add_node("writer", node_writer)
    
    # Definir flujo
    graph.add_edge(START, "scout")
    graph.add_edge("scout", "analyst")
    graph.add_edge("analyst", "visualizer")
    graph.add_edge("visualizer", "writer")
    graph.add_edge("writer", END)
    
    return graph.compile()


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="ChatDT - The Agentic Football Analyst",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py --team 451           # Analizar ultimo partido de Boca
  python main.py --fixture 971362     # Analizar partido especifico
  python main.py                      # Usar datos en cache
        """
    )
    
    parser.add_argument("--team", type=int, help="ID del equipo (ej: 451=Boca, 435=River)")
    parser.add_argument("--fixture", type=int, help="ID del partido especifico")
    parser.add_argument("--no-viz", action="store_true", help="Saltar visualizacion")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  ChatDT - The Agentic Football Analyst")
    print(f"  Powered by LangGraph + {LLM_PROVIDER.upper()}")
    print("=" * 70)
    
    # Construir y ejecutar grafo
    app = build_graph()
    
    # Estado inicial
    initial_state: AgentState = {
        "fixture_id": args.fixture,
        "team_id": args.team,
        "raw_data": None,
        "match_info": None,
        "analysis": None,
        "cps_scores": None,
        "visualization_path": None,
        "report_markdown": None,
        "report_path": None,
        "errors": [],
        "status": "starting"
    }
    
    # Ejecutar pipeline
    print("\n[PIPELINE] Iniciando flujo de agentes...")
    print("  Scout -> Analyst -> Visualizer -> Writer")
    
    try:
        final_state = app.invoke(initial_state)
        
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETADO")
        print("=" * 70)
        
        if final_state.get("errors"):
            print("\nErrores encontrados:")
            for error in final_state["errors"]:
                print(f"  - {error}")
        
        print(f"\nEstado final: {final_state.get('status')}")
        print(f"Reporte: {final_state.get('report_path')}")
        print(f"Visualizacion: {final_state.get('visualization_path')}")
        
        # Mostrar preview del reporte
        if final_state.get("report_markdown"):
            print("\n" + "-" * 70)
            print("PREVIEW DEL REPORTE:")
            print("-" * 70)
            # Mostrar primeras 30 lineas
            lines = final_state["report_markdown"].split("\n")[:30]
            print("\n".join(lines))
            if len(final_state["report_markdown"].split("\n")) > 30:
                print("\n... (reporte completo en el archivo)")
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline fallido: {e}")
        raise


if __name__ == "__main__":
    main()

