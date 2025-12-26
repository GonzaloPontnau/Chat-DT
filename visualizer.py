"""
ChatDT - Fase 4: El Agente Visualizador

Este modulo genera visualizaciones del analisis de partidos:
- Formaciones tacticas sobre una cancha de futbol
- Radar Chart comparativo de metricas
- Imagen combinada de analisis

Usa mplsoccer para dibujar canchas profesionales.

Uso:
    from visualizer import VisualizerAgent
    
    viz = VisualizerAgent()
    viz.create_match_report("data/raw/match_full_971362.json")
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from mplsoccer import Pitch, VerticalPitch

# Configuracion de colores
COLORS = {
    "home": "#1E88E5",      # Azul
    "away": "#E53935",      # Rojo
    "home_light": "#90CAF9",
    "away_light": "#EF9A9A",
    "pitch": "#2E7D32",     # Verde oscuro
    "background": "#1a1a2e",
    "text": "#FFFFFF",
    "grid": "#333355",
}

# Directorio de salida
OUTPUT_DIR = Path("data/visualizations")


class VisualizerAgent:
    """
    Agente Visualizador: Genera graficos del analisis de partidos.
    
    Crea:
    - Formaciones tacticas (pitch plot)
    - Radar charts comparativos
    - Reportes visuales combinados
    """
    
    def __init__(self, style: str = "dark"):
        """
        Inicializa el Visualizer.
        
        Args:
            style: "dark" o "light" para el tema visual
        """
        self.style = style
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configurar estilo de matplotlib
        if style == "dark":
            plt.style.use('dark_background')
        else:
            plt.style.use('seaborn-v0_8-whitegrid')
    
    def load_match_data(self, filepath: str) -> Dict[str, Any]:
        """Carga datos del partido desde JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_grid_position(self, grid: str) -> Tuple[float, float]:
        """
        Convierte grid de la API a coordenadas de cancha.
        
        Grid format: "row:col" donde:
        - row 1 = arquero
        - row 2 = defensores
        - row 3 = mediocampistas
        - row 4-5 = delanteros
        
        Args:
            grid: String como "2:3"
            
        Returns:
            (x, y) coordenadas para plotear
        """
        if not grid:
            return (50, 50)
        
        try:
            row, col = grid.split(":")
            row = int(row)
            col = int(col)
        except:
            return (50, 50)
        
        # Mapear row a posicion Y (0-100, donde 0 es el arco propio)
        row_positions = {
            1: 5,    # Arquero
            2: 20,   # Defensores
            3: 45,   # Mediocampistas defensivos
            4: 65,   # Mediocampistas ofensivos
            5: 85,   # Delanteros
        }
        y = row_positions.get(row, 50)
        
        # Mapear col a posicion X (0-100)
        # col 1 = izquierda, col 4-5 = derecha
        # Asumimos max 5 jugadores por linea
        x = (col - 1) * 25 + 12.5  # Distribuir uniformemente
        
        return (x, y)
    
    def draw_formation(
        self,
        ax,
        lineup: Dict[str, Any],
        is_home: bool = True,
        pitch_length: float = 120,
        pitch_width: float = 80
    ):
        """
        Dibuja la formacion de un equipo sobre el pitch.
        
        Args:
            ax: Axes de matplotlib
            lineup: Datos del lineup de la API
            is_home: True para equipo local (abajo), False para visitante (arriba)
            pitch_length: Largo de la cancha
            pitch_width: Ancho de la cancha
        """
        team_name = lineup.get("team", {}).get("name", "Team")
        formation = lineup.get("formation", "")
        players = lineup.get("startXI", [])
        
        color = COLORS["home"] if is_home else COLORS["away"]
        
        for player_data in players:
            player = player_data.get("player", {})
            grid = player.get("grid", "")
            name = player.get("name", "")
            number = player.get("number", "")
            
            # Obtener coordenadas
            x_pct, y_pct = self.parse_grid_position(grid)
            
            # Convertir porcentaje a coordenadas de cancha
            x = (x_pct / 100) * pitch_width
            
            if is_home:
                y = (y_pct / 100) * (pitch_length / 2)
            else:
                y = pitch_length - (y_pct / 100) * (pitch_length / 2)
            
            # Dibujar circulo del jugador
            circle = plt.Circle(
                (x, y), 
                radius=2.5,
                color=color, 
                ec='white', 
                linewidth=1.5,
                zorder=10
            )
            ax.add_patch(circle)
            
            # Numero del jugador
            ax.text(
                x, y, 
                str(number), 
                ha='center', va='center',
                fontsize=8, fontweight='bold',
                color='white',
                zorder=11
            )
            
            # Nombre (abreviado)
            short_name = name.split()[-1][:10] if name else ""
            y_offset = -4 if is_home else 4
            ax.text(
                x, y + y_offset,
                short_name,
                ha='center', va='center',
                fontsize=6,
                color='white',
                alpha=0.9,
                zorder=11
            )
        
        # Etiqueta de formacion
        label_y = 5 if is_home else pitch_length - 5
        ax.text(
            pitch_width / 2, label_y,
            f"{team_name} ({formation})",
            ha='center', va='center',
            fontsize=10, fontweight='bold',
            color=color,
            zorder=12
        )
    
    def create_pitch_plot(
        self,
        lineups: List[Dict],
        match_info: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Crea el grafico de la cancha con ambas formaciones.
        
        Args:
            lineups: Lista de lineups de la API
            match_info: Info del partido
            save_path: Ruta para guardar (opcional)
            
        Returns:
            Figure de matplotlib
        """
        # Crear cancha vertical
        pitch = VerticalPitch(
            pitch_type='statsbomb',
            pitch_color=COLORS["pitch"],
            line_color='white',
            linewidth=1,
            goal_type='box'
        )
        
        fig, ax = pitch.draw(figsize=(10, 14))
        fig.patch.set_facecolor(COLORS["background"])
        
        # Titulo
        home = match_info.get('home_team', 'Home')
        away = match_info.get('away_team', 'Away')
        home_goals = match_info.get('home_goals', 0)
        away_goals = match_info.get('away_goals', 0)
        
        fig.suptitle(
            f"{home} {home_goals} - {away_goals} {away}",
            fontsize=16, fontweight='bold',
            color=COLORS["text"],
            y=0.98
        )
        
        # Dibujar formaciones
        if len(lineups) >= 1:
            self.draw_formation(ax, lineups[0], is_home=True)
        if len(lineups) >= 2:
            self.draw_formation(ax, lineups[1], is_home=False)
        
        # Leyenda
        home_patch = mpatches.Patch(color=COLORS["home"], label=home)
        away_patch = mpatches.Patch(color=COLORS["away"], label=away)
        ax.legend(
            handles=[home_patch, away_patch],
            loc='upper right',
            fontsize=8,
            facecolor=COLORS["background"],
            edgecolor='white'
        )
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor=COLORS["background"])
            print(f"  [SAVE] {save_path}")
        
        return fig
    
    def create_radar_chart(
        self,
        stats: Dict[str, Dict],
        match_info: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Crea un radar chart comparando metricas de ambos equipos.
        
        Args:
            stats: Estadisticas parseadas del partido
            match_info: Info del partido
            save_path: Ruta para guardar
            
        Returns:
            Figure de matplotlib
        """
        # Metricas para el radar
        metrics = [
            ("Shots on Goal", "shots_on_goal", 10),
            ("Shots Inside Box", "shots_inside_box", 15),
            ("Possession %", "possession", 100),
            ("Pass Accuracy %", "pass_accuracy", 100),
            ("Corner Kicks", "corner_kicks", 10),
            ("Fouls", "fouls", 30),  # Invertido (menos es mejor)
        ]
        
        labels = [m[0] for m in metrics]
        num_vars = len(metrics)
        
        # Calcular angulos
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Cerrar el poligono
        
        # Obtener valores normalizados
        home_values = []
        away_values = []
        
        for label, key, max_val in metrics:
            home_val = stats.get("home", {}).get(key, 0)
            away_val = stats.get("away", {}).get(key, 0)
            
            # Invertir fouls (menos es mejor)
            if key == "fouls":
                home_val = max_val - home_val
                away_val = max_val - away_val
            
            # Normalizar a 0-1
            home_values.append(min(home_val / max_val, 1.0))
            away_values.append(min(away_val / max_val, 1.0))
        
        # Cerrar poligonos
        home_values += home_values[:1]
        away_values += away_values[:1]
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor(COLORS["background"])
        ax.set_facecolor(COLORS["background"])
        
        # Dibujar radar
        ax.plot(angles, home_values, 'o-', linewidth=2, 
               label=match_info.get('home_team', 'Home'),
               color=COLORS["home"])
        ax.fill(angles, home_values, alpha=0.25, color=COLORS["home"])
        
        ax.plot(angles, away_values, 'o-', linewidth=2,
               label=match_info.get('away_team', 'Away'),
               color=COLORS["away"])
        ax.fill(angles, away_values, alpha=0.25, color=COLORS["away"])
        
        # Configurar ejes
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=9, color=COLORS["text"])
        ax.set_ylim(0, 1)
        
        # Estilo
        ax.spines['polar'].set_color(COLORS["grid"])
        ax.grid(color=COLORS["grid"], alpha=0.5)
        ax.tick_params(colors=COLORS["text"])
        
        # Titulo y leyenda
        ax.set_title(
            "Comparacion de Rendimiento",
            size=14, fontweight='bold',
            color=COLORS["text"],
            pad=20
        )
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1),
                 facecolor=COLORS["background"], edgecolor='white')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor=COLORS["background"])
            print(f"  [SAVE] {save_path}")
        
        return fig
    
    def create_cps_bar_chart(
        self,
        cps_scores: Dict[str, Dict],
        match_info: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Crea un grafico de barras del CPS Score desglosado.
        
        Args:
            cps_scores: Scores CPS del Analyst
            match_info: Info del partido
            save_path: Ruta para guardar
            
        Returns:
            Figure de matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor(COLORS["background"])
        ax.set_facecolor(COLORS["background"])
        
        home = match_info.get('home_team', 'Home')
        away = match_info.get('away_team', 'Away')
        
        categories = ['Threat', 'Control', 'Friction', 'TOTAL']
        home_scores = [
            cps_scores['home']['threat'],
            cps_scores['home']['control'],
            cps_scores['home']['friction'],
            cps_scores['home']['total']
        ]
        away_scores = [
            cps_scores['away']['threat'],
            cps_scores['away']['control'],
            cps_scores['away']['friction'],
            cps_scores['away']['total']
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, home_scores, width, 
                      label=home, color=COLORS["home"])
        bars2 = ax.bar(x + width/2, away_scores, width,
                      label=away, color=COLORS["away"])
        
        # Etiquetas
        ax.set_xlabel('Componente CPS', color=COLORS["text"])
        ax.set_ylabel('Puntos', color=COLORS["text"])
        ax.set_title('ChatDT Performance Score (CPS)', 
                    fontweight='bold', color=COLORS["text"])
        ax.set_xticks(x)
        ax.set_xticklabels(categories, color=COLORS["text"])
        ax.tick_params(colors=COLORS["text"])
        ax.legend(facecolor=COLORS["background"], edgecolor='white')
        
        # Valores sobre las barras
        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=8, color=COLORS["text"])
        
        autolabel(bars1)
        autolabel(bars2)
        
        # Linea en cero para Friction
        ax.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor=COLORS["background"])
            print(f"  [SAVE] {save_path}")
        
        return fig
    
    def create_match_report(
        self,
        match_filepath: str,
        analysis_filepath: Optional[str] = None
    ) -> str:
        """
        Genera un reporte visual completo del partido.
        
        Crea una imagen combinada con:
        - Formaciones tacticas
        - Radar chart
        - CPS breakdown
        
        Args:
            match_filepath: Ruta al JSON del partido
            analysis_filepath: Ruta al JSON del analisis (opcional)
            
        Returns:
            Ruta de la imagen generada
        """
        print("\n[VISUALIZER] Generando reporte visual...")
        
        # Cargar datos
        match_data = self.load_match_data(match_filepath)
        
        # Extraer info
        fixture = match_data.get("fixture", {})
        fixture_id = match_data.get("fixture_id", "unknown")
        teams = fixture.get("teams", {})
        goals = fixture.get("goals", {})
        lineups = match_data.get("lineups", [])
        
        match_info = {
            "fixture_id": fixture_id,
            "home_team": teams.get("home", {}).get("name", "Home"),
            "away_team": teams.get("away", {}).get("name", "Away"),
            "home_goals": goals.get("home", 0),
            "away_goals": goals.get("away", 0),
        }
        
        print(f"  Partido: {match_info['home_team']} vs {match_info['away_team']}")
        
        # Cargar analisis si existe
        if analysis_filepath and Path(analysis_filepath).exists():
            with open(analysis_filepath, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
        else:
            # Generar analisis on-the-fly
            from analyst import AnalystAgent
            analyst = AnalystAgent()
            analysis = analyst.analyze_match(match_filepath)
        
        # Crear figura combinada
        fig = plt.figure(figsize=(20, 14))
        fig.patch.set_facecolor(COLORS["background"])
        
        gs = GridSpec(2, 2, figure=fig, height_ratios=[1.2, 1])
        
        # 1. Formaciones (arriba izquierda)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.set_facecolor(COLORS["background"])
        
        if lineups:
            pitch = VerticalPitch(
                pitch_type='statsbomb',
                pitch_color=COLORS["pitch"],
                line_color='white',
                linewidth=1
            )
            pitch.draw(ax=ax1)
            
            if len(lineups) >= 1:
                self.draw_formation(ax1, lineups[0], is_home=True)
            if len(lineups) >= 2:
                self.draw_formation(ax1, lineups[1], is_home=False)
            
            ax1.set_title("Formaciones Tacticas", 
                         fontweight='bold', color=COLORS["text"], pad=10)
        
        # 2. Radar Chart (arriba derecha)
        ax2 = fig.add_subplot(gs[0, 1], polar=True)
        self._draw_radar_on_ax(ax2, analysis['stats'], match_info)
        
        # 3. CPS Breakdown (abajo izquierda)
        ax3 = fig.add_subplot(gs[1, 0])
        self._draw_cps_bars_on_ax(ax3, analysis['cps_scores'], match_info)
        
        # 4. Veredicto (abajo derecha)
        ax4 = fig.add_subplot(gs[1, 1])
        self._draw_verdict_on_ax(ax4, analysis, match_info)
        
        # Titulo general
        fig.suptitle(
            f"ChatDT Match Analysis - {match_info['home_team']} {match_info['home_goals']}-{match_info['away_goals']} {match_info['away_team']}",
            fontsize=18, fontweight='bold',
            color=COLORS["text"],
            y=0.98
        )
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Guardar
        output_path = OUTPUT_DIR / f"match_analysis_{fixture_id}.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor=COLORS["background"])
        
        print(f"  [SAVE] Reporte guardado: {output_path}")
        
        plt.close(fig)
        
        return str(output_path)
    
    def _draw_radar_on_ax(self, ax, stats: Dict, match_info: Dict):
        """Helper para dibujar radar en un ax existente."""
        metrics = [
            ("Shots", "shots_on_goal", 10),
            ("Inside Box", "shots_inside_box", 15),
            ("Possession", "possession", 100),
            ("Pass Acc", "pass_accuracy", 100),
            ("Corners", "corner_kicks", 10),
        ]
        
        labels = [m[0] for m in metrics]
        num_vars = len(metrics)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]
        
        home_values = []
        away_values = []
        
        for label, key, max_val in metrics:
            home_val = stats.get("home", {}).get(key, 0)
            away_val = stats.get("away", {}).get(key, 0)
            home_values.append(min(home_val / max_val, 1.0))
            away_values.append(min(away_val / max_val, 1.0))
        
        home_values += home_values[:1]
        away_values += away_values[:1]
        
        ax.set_facecolor(COLORS["background"])
        ax.plot(angles, home_values, 'o-', linewidth=2, color=COLORS["home"])
        ax.fill(angles, home_values, alpha=0.25, color=COLORS["home"])
        ax.plot(angles, away_values, 'o-', linewidth=2, color=COLORS["away"])
        ax.fill(angles, away_values, alpha=0.25, color=COLORS["away"])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=8, color=COLORS["text"])
        ax.set_ylim(0, 1)
        ax.spines['polar'].set_color(COLORS["grid"])
        ax.grid(color=COLORS["grid"], alpha=0.5)
        ax.tick_params(colors=COLORS["text"])
        ax.set_title("Performance Radar", fontweight='bold', 
                    color=COLORS["text"], pad=15)
    
    def _draw_cps_bars_on_ax(self, ax, cps_scores: Dict, match_info: Dict):
        """Helper para dibujar barras CPS en un ax existente."""
        ax.set_facecolor(COLORS["background"])
        
        categories = ['Threat', 'Control', 'Friction', 'TOTAL']
        home_scores = [cps_scores['home'][k.lower()] for k in categories]
        away_scores = [cps_scores['away'][k.lower()] for k in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax.bar(x - width/2, home_scores, width, 
              label=match_info['home_team'], color=COLORS["home"])
        ax.bar(x + width/2, away_scores, width,
              label=match_info['away_team'], color=COLORS["away"])
        
        ax.set_ylabel('Puntos', color=COLORS["text"])
        ax.set_title('CPS Breakdown', fontweight='bold', color=COLORS["text"])
        ax.set_xticks(x)
        ax.set_xticklabels(categories, color=COLORS["text"])
        ax.tick_params(colors=COLORS["text"])
        ax.legend(fontsize=8, facecolor=COLORS["background"], edgecolor='white')
        ax.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
    
    def _draw_verdict_on_ax(self, ax, analysis: Dict, match_info: Dict):
        """Helper para mostrar el veredicto en un ax."""
        ax.set_facecolor(COLORS["background"])
        ax.axis('off')
        
        home = match_info['home_team']
        away = match_info['away_team']
        home_cps = analysis['cps_scores']['home']['total']
        away_cps = analysis['cps_scores']['away']['total']
        verdict = analysis.get('verdict', '')
        
        text = f"""
RESULTADO FINAL
{home} {match_info['home_goals']} - {match_info['away_goals']} {away}

CPS SCORES
{home}: {home_cps:.1f}
{away}: {away_cps:.1f}

VEREDICTO
{verdict}
        """
        
        ax.text(0.5, 0.5, text.strip(),
               transform=ax.transAxes,
               fontsize=11,
               verticalalignment='center',
               horizontalalignment='center',
               color=COLORS["text"],
               family='monospace',
               bbox=dict(boxstyle='round', facecolor=COLORS["grid"], alpha=0.8))
        
        ax.set_title("Match Verdict", fontweight='bold', 
                    color=COLORS["text"], pad=10)


def main():
    """Script de prueba para el Visualizer Agent."""
    print("=" * 70)
    print("ChatDT - Visualizer Agent Test (Fase 4)")
    print("=" * 70)
    
    viz = VisualizerAgent(style="dark")
    
    # Buscar archivos de partidos
    raw_dir = Path("data/raw")
    match_files = list(raw_dir.glob("match_full_*.json"))
    
    if not match_files:
        print("\n[ERROR] No hay archivos de partidos en data/raw/")
        print("Ejecuta primero: python scout.py")
        return
    
    match_file = match_files[0]
    print(f"\nGenerando visualizaciones para: {match_file}")
    
    # Generar reporte completo
    output_path = viz.create_match_report(str(match_file))
    
    print("\n" + "=" * 70)
    print("FASE 4 COMPLETADA")
    print("=" * 70)
    print(f"Imagen generada: {output_path}")
    print("\nAbre la imagen para ver el analisis visual completo.")


if __name__ == "__main__":
    main()

