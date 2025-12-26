"""
ChatDT: The Agentic Football Analyst
=====================================
Frontend - Match Command Center

Un dashboard de analisis tactico con estetica de "War Room" deportivo.
Diseñado para parecer el centro de operaciones de un Director Tecnico profesional.
"""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime

# Importar agentes
from scout import ScoutAgent
from analyst import AnalystAgent
from visualizer import VisualizerAgent

# Configuracion de pagina
st.set_page_config(
    page_title="ChatDT | Match Command Center",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS - ESTETICA "WAR ROOM" / COMMAND CENTER
# =============================================================================
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Root variables */
    :root {
        --bg-dark: #0a0e17;
        --bg-card: #111827;
        --bg-card-hover: #1a2332;
        --accent-green: #00ff88;
        --accent-gold: #ffd700;
        --accent-red: #ff4757;
        --accent-blue: #00d4ff;
        --text-primary: #ffffff;
        --text-secondary: #8b9dc3;
        --border-glow: rgba(0, 255, 136, 0.3);
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0e17 0%, #1a1a2e 50%, #0f1419 100%);
        background-attachment: fixed;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0a0e17 100%);
        border-right: 1px solid var(--border-glow);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-secondary);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Orbitron', monospace !important;
        color: var(--text-primary) !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    h1 {
        background: linear-gradient(90deg, var(--accent-green), var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
    }
    
    /* Regular text */
    p, span, div {
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* Code and metrics */
    code, .stMetric {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #111827, #1a2332);
        border: 1px solid var(--border-glow);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 255, 136, 0.1);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 255, 136, 0.2);
        border-color: var(--accent-green);
    }
    
    [data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--accent-green) !important;
        font-family: 'Orbitron', monospace !important;
        font-size: 32px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88, #00d4ff);
        color: #0a0e17 !important;
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        border: none;
        border-radius: 8px;
        padding: 12px 30px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 255, 136, 0.5);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--bg-card);
        border: 1px solid var(--border-glow);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border: 1px solid var(--border-glow);
        border-radius: 8px;
        color: var(--text-primary) !important;
        font-family: 'Rajdhani', sans-serif;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--bg-card);
        border: 1px solid var(--border-glow);
        border-radius: 8px 8px 0 0;
        color: var(--text-secondary);
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 212, 255, 0.2));
        border-color: var(--accent-green);
        color: var(--accent-green) !important;
    }
    
    /* Cards container */
    .card {
        background: linear-gradient(145deg, #111827, #1a2332);
        border: 1px solid var(--border-glow);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Score display */
    .score-display {
        font-family: 'Orbitron', monospace;
        font-size: 72px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(90deg, var(--accent-green), var(--accent-gold));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(0, 255, 136, 0.5);
    }
    
    /* Team names */
    .team-name {
        font-family: 'Orbitron', monospace;
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
        text-transform: uppercase;
        letter-spacing: 3px;
    }
    
    /* CPS Progress bars */
    .cps-bar {
        height: 12px;
        border-radius: 6px;
        background: linear-gradient(90deg, var(--accent-green), var(--accent-blue));
        box-shadow: 0 0 10px var(--accent-green);
        transition: width 1s ease-out;
    }
    
    /* Glowing borders */
    .glow-border {
        border: 2px solid var(--accent-green);
        box-shadow: 0 0 15px var(--border-glow), inset 0 0 15px rgba(0, 255, 136, 0.05);
    }
    
    /* Animated pulse */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Status indicator */
    .status-live {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: var(--accent-red);
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 1s ease-in-out infinite;
    }
    
    .status-complete {
        display: inline-block;
        width: 10px;
        height: 10px;
        background: var(--accent-green);
        border-radius: 50%;
        margin-right: 8px;
    }
    
    /* Markdown styling */
    .stMarkdown {
        color: var(--text-secondary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-green);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-blue);
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# HEADER
# =============================================================================
def render_header():
    """Renderiza el header principal con logo y estado del sistema."""
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <span style="font-size: 48px;">⚽</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <h1 style="margin: 0; font-size: 42px;">CHAT<span style="color: #00ff88;">DT</span></h1>
            <p style="color: #8b9dc3; font-family: 'Rajdhani', sans-serif; font-size: 16px; letter-spacing: 4px; margin-top: -10px;">
                MATCH COMMAND CENTER
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 15px;">
            <span class="status-complete"></span>
            <span style="color: #00ff88; font-family: 'JetBrains Mono', monospace; font-size: 12px;">ONLINE</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid rgba(0, 255, 136, 0.2); margin: 20px 0;'>", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar():
    """Renderiza el sidebar con controles de seleccion."""
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <span style="font-family: 'Orbitron', monospace; color: #00ff88; font-size: 14px; letter-spacing: 2px;">
                CONTROL PANEL
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Modo de analisis
        st.markdown("##### MODO DE ANALISIS")
        analysis_mode = st.radio(
            "Seleccionar modo",
            ["Por Fixture ID", "Por Equipo"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if analysis_mode == "Por Fixture ID":
            st.markdown("##### FIXTURE ID")
            fixture_id = st.number_input(
                "ID del partido",
                min_value=1,
                value=971362,
                step=1,
                label_visibility="collapsed"
            )
            team_id = None
        else:
            st.markdown("##### EQUIPO")
            teams = {
                "Boca Juniors": 451,
                "River Plate": 435,
                "Racing Club": 463,
                "Independiente": 459,
                "San Lorenzo": 474,
                "Estudiantes LP": 465,
                "Velez Sarsfield": 478,
                "Argentinos Jrs": 458,
            }
            selected_team = st.selectbox(
                "Seleccionar equipo",
                list(teams.keys()),
                label_visibility="collapsed"
            )
            team_id = teams[selected_team]
            fixture_id = None
        
        st.markdown("---")
        
        # Boton de analisis
        analyze_button = st.button(
            "INICIAR ANALISIS",
            use_container_width=True,
            type="primary"
        )
        
        st.markdown("---")
        
        # Info del sistema
        st.markdown("""
        <div style="padding: 15px; background: rgba(0, 255, 136, 0.05); border-radius: 8px; border: 1px solid rgba(0, 255, 136, 0.2);">
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8b9dc3; margin: 0;">
                <strong style="color: #00ff88;">SISTEMA</strong><br>
                Liga: Argentina<br>
                Temporada: 2023<br>
                LLM: Groq/Gemini
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        return analyze_button, fixture_id, team_id


# =============================================================================
# SCORE DISPLAY
# =============================================================================
def render_score_display(match_info):
    """Renderiza el marcador del partido con estilo."""
    
    home = match_info.get('home_team', 'Local')
    away = match_info.get('away_team', 'Visitante')
    home_goals = match_info.get('home_goals', 0)
    away_goals = match_info.get('away_goals', 0)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1a2332);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 16px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1; text-align: center;">
                <p style="font-family: 'Orbitron', monospace; font-size: 20px; color: #fff; text-transform: uppercase; letter-spacing: 2px; margin: 0;">
                    {home}
                </p>
            </div>
            <div style="flex: 1; text-align: center;">
                <p style="font-family: 'Orbitron', monospace; font-size: 72px; font-weight: 900; margin: 0;
                    background: linear-gradient(90deg, #00ff88, #ffd700);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;">
                    {home_goals} - {away_goals}
                </p>
            </div>
            <div style="flex: 1; text-align: center;">
                <p style="font-family: 'Orbitron', monospace; font-size: 20px; color: #fff; text-transform: uppercase; letter-spacing: 2px; margin: 0;">
                    {away}
                </p>
            </div>
        </div>
        <div style="text-align: center; margin-top: 15px;">
            <span class="status-complete"></span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #8b9dc3;">
                FINALIZADO | {match_info.get('date', 'N/A')} | {match_info.get('venue', 'N/A')}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# CPS SCORE DISPLAY
# =============================================================================
def render_cps_comparison(cps_scores, match_info):
    """Renderiza la comparacion de CPS scores con barras animadas."""
    
    home = match_info.get('home_team', 'Local')
    away = match_info.get('away_team', 'Visitante')
    
    home_cps = cps_scores.get('home', {})
    away_cps = cps_scores.get('away', {})
    
    home_total = home_cps.get('TOTAL', 0)
    away_total = away_cps.get('TOTAL', 0)
    max_cps = max(home_total, away_total, 1)
    
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #111827, #1a2332);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
    ">
        <h3 style="text-align: center; margin-bottom: 20px; font-size: 18px;">
            CPS PERFORMANCE SCORE
        </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label=home,
            value=f"{home_total:.1f}",
            delta=f"+{home_total - away_total:.1f}" if home_total > away_total else f"{home_total - away_total:.1f}"
        )
        
        # Breakdown
        for metric in ['Threat', 'Control', 'Friction']:
            value = home_cps.get(metric, 0)
            st.markdown(f"""
            <div style="margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-family: 'Rajdhani', sans-serif; color: #8b9dc3; font-size: 13px;">{metric.upper()}</span>
                    <span style="font-family: 'JetBrains Mono', monospace; color: {'#00ff88' if value >= 0 else '#ff4757'}; font-size: 13px;">{value:+.1f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.metric(
            label=away,
            value=f"{away_total:.1f}",
            delta=f"+{away_total - home_total:.1f}" if away_total > home_total else f"{away_total - home_total:.1f}"
        )
        
        # Breakdown
        for metric in ['Threat', 'Control', 'Friction']:
            value = away_cps.get(metric, 0)
            st.markdown(f"""
            <div style="margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-family: 'Rajdhani', sans-serif; color: #8b9dc3; font-size: 13px;">{metric.upper()}</span>
                    <span style="font-family: 'JetBrains Mono', monospace; color: {'#00ff88' if value >= 0 else '#ff4757'}; font-size: 13px;">{value:+.1f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================
def run_analysis(fixture_id=None, team_id=None):
    """Ejecuta el pipeline de analisis completo."""
    
    # Progress container
    progress_container = st.empty()
    
    with progress_container.container():
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #111827, #1a2332);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 16px;
            padding: 30px;
            text-align: center;
        ">
            <div class="pulse">
                <span style="font-size: 48px;">🔍</span>
            </div>
            <p style="font-family: 'Orbitron', monospace; color: #00ff88; margin-top: 20px;">
                ANALIZANDO PARTIDO...
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    try:
        # 1. Scout Agent
        scout = ScoutAgent(source="api-football")
        
        if fixture_id:
            raw_data = scout.get_match_data(fixture_id)
        elif team_id:
            matches = scout.get_last_matches(team_id, num_matches=1)
            if matches:
                fixture_id = matches[0]['fixture']['id']
                raw_data = scout.get_match_data(fixture_id)
            else:
                st.error("No se encontraron partidos para este equipo.")
                return None
        
        if not raw_data:
            st.error("No se pudo obtener datos del partido.")
            return None
        
        # Extract match info
        fixture = raw_data.get('fixture', {})
        teams = raw_data.get('teams', {})
        goals = raw_data.get('goals', {})
        
        match_info = {
            'fixture_id': fixture.get('id'),
            'home_team': teams.get('home', {}).get('name', 'Local'),
            'away_team': teams.get('away', {}).get('name', 'Visitante'),
            'home_goals': goals.get('home', 0),
            'away_goals': goals.get('away', 0),
            'date': fixture.get('date', '')[:10],
            'venue': fixture.get('venue', {}).get('name', 'N/A'),
        }
        
        # 2. Analyst Agent
        analyst = AnalystAgent()
        analysis = analyst.analyze_match(raw_data)
        
        cps_scores = {
            'home': analysis.get('home_cps', {}),
            'away': analysis.get('away_cps', {}),
            'verdict': analysis.get('verdict', '')
        }
        
        # 3. Visualizer Agent
        visualizer = VisualizerAgent()
        viz_path = visualizer.generate_match_report(raw_data)
        
        # 4. Generate report (simplified for UI)
        report = generate_ui_report(match_info, cps_scores, raw_data)
        
        progress_container.empty()
        
        return {
            'match_info': match_info,
            'cps_scores': cps_scores,
            'viz_path': viz_path,
            'report': report,
            'raw_data': raw_data
        }
        
    except Exception as e:
        progress_container.empty()
        st.error(f"Error en el analisis: {str(e)}")
        return None


def generate_ui_report(match_info, cps_scores, raw_data):
    """Genera un reporte simplificado para la UI."""
    
    home = match_info['home_team']
    away = match_info['away_team']
    home_cps = cps_scores['home'].get('TOTAL', 0)
    away_cps = cps_scores['away'].get('TOTAL', 0)
    
    winner = home if home_cps > away_cps else away
    diff = abs(home_cps - away_cps)
    
    return f"""
**{home}** registro un CPS de **{home_cps:.1f}** puntos, mientras que **{away}** 
alcanzo **{away_cps:.1f}** puntos. 

La diferencia de **{diff:.1f}** puntos indica que **{winner}** tuvo un rendimiento 
superior en el partido, independientemente del resultado final.

El CPS Score evalua tres dimensiones clave:
- **Threat**: Peligro ofensivo generado (tiros, corners, oportunidades)
- **Control**: Dominio del juego (posesion, precision de pases)
- **Friction**: Impacto negativo (faltas, tarjetas)
"""


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    """Funcion principal de la aplicacion."""
    
    # Header
    render_header()
    
    # Sidebar
    analyze_button, fixture_id, team_id = render_sidebar()
    
    # Initialize session state
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    
    # Run analysis
    if analyze_button:
        result = run_analysis(fixture_id=fixture_id, team_id=team_id)
        if result:
            st.session_state.analysis_result = result
    
    # Display results
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
        # Score display
        render_score_display(result['match_info'])
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["CPS ANALYSIS", "TACTICAL VIEW", "MATCH REPORT"])
        
        with tab1:
            render_cps_comparison(result['cps_scores'], result['match_info'])
            
            # Verdict
            st.markdown(f"""
            <div style="
                background: linear-gradient(145deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1));
                border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            ">
                <h4 style="color: #00ff88; font-family: 'Orbitron', monospace; font-size: 14px; margin-bottom: 10px;">
                    VEREDICTO DEL SISTEMA
                </h4>
                <p style="color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 16px; line-height: 1.6;">
                    {result['cps_scores'].get('verdict', 'Analisis completado.')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with tab2:
            if result['viz_path'] and os.path.exists(result['viz_path']):
                st.image(result['viz_path'], use_container_width=True)
            else:
                st.info("Visualizacion tactica no disponible.")
        
        with tab3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(145deg, #111827, #1a2332);
                border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 16px;
                padding: 24px;
            ">
                <h4 style="color: #00ff88; font-family: 'Orbitron', monospace; font-size: 14px; margin-bottom: 15px;">
                    ANALISIS DETALLADO
                </h4>
                <div style="color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 16px; line-height: 1.8;">
                    {result['report']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Welcome state
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #111827, #1a2332);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            margin: 40px 0;
        ">
            <span style="font-size: 80px; display: block; margin-bottom: 20px;">⚽</span>
            <h2 style="color: #fff; font-family: 'Orbitron', monospace; font-size: 24px; margin-bottom: 15px;">
                MATCH COMMAND CENTER
            </h2>
            <p style="color: #8b9dc3; font-family: 'Rajdhani', sans-serif; font-size: 18px; max-width: 500px; margin: 0 auto 30px;">
                Selecciona un partido o equipo en el panel lateral para iniciar el analisis tactico con inteligencia artificial.
            </p>
            <div style="display: flex; justify-content: center; gap: 40px; margin-top: 30px;">
                <div>
                    <span style="font-size: 32px;">📊</span>
                    <p style="color: #00ff88; font-family: 'JetBrains Mono', monospace; font-size: 12px; margin-top: 8px;">CPS SCORE</p>
                </div>
                <div>
                    <span style="font-size: 32px;">🎯</span>
                    <p style="color: #00ff88; font-family: 'JetBrains Mono', monospace; font-size: 12px; margin-top: 8px;">TACTICAL VIEW</p>
                </div>
                <div>
                    <span style="font-size: 32px;">📝</span>
                    <p style="color: #00ff88; font-family: 'JetBrains Mono', monospace; font-size: 12px; margin-top: 8px;">AI REPORT</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

