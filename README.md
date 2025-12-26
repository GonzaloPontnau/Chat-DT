# ChatDT: The Agentic Football Analyst

> **Beyond the Scoreboard: Automating Tactical Analysis with Multi-Agent Systems.**

Un sistema de **IA Multi-Agente** que analiza partidos de la Liga Profesional Argentina usando LangGraph, genera metricas de rendimiento propias (CPS Score), crea visualizaciones tacticas y escribe cronicas periodisticas automaticamente.

---

## Que hace ChatDT?

ChatDT responde una pregunta que el marcador no puede: **Quien jugo mejor?**

```
Input:  ID de un partido (ej: Boca vs Atletico Tucuman)
Output: - Analisis numerico con CPS Score
        - Visualizacion tactica (formaciones + radar chart)
        - Cronica periodistica generada por IA
```

### Ejemplo de Output

**Cronica generada automaticamente:**

> *"El Xeneize se impuso en la Bombonera con una victoria de 1-0. Con un CPS de 103.8 frente a 60.0, Boca demostro superioridad en control (75.1) y amenaza ofensiva (38.2). Oscar Romero definio el encuentro en el minuto 69..."*

---

## Arquitectura del Sistema

```
                    LangGraph StateGraph
                           |
     +---------------------+---------------------+
     |                     |                     |
     v                     v                     v
+---------+          +-----------+         +------------+
|  SCOUT  |  ------> |  ANALYST  | ------> | VISUALIZER |
| (Datos) |          |   (CPS)   |         |  (Graficos)|
+---------+          +-----------+         +------------+
                                                  |
                                                  v
                                            +----------+
                                            |  WRITER  |
                                            |  (LLM)   |
                                            +----------+
                                                  |
                                                  v
                                           [Cronica.md]
```

### Agentes

| Agente | Rol | Tecnologia |
|--------|-----|------------|
| **Scout** | Ingesta de datos de partidos | API-FOOTBALL |
| **Analyst** | Calcula el CPS Score | Pandas + Python |
| **Visualizer** | Genera graficos tacticos | mplsoccer + matplotlib |
| **Writer** | Escribe cronica periodistica | Groq/Gemini (gratis) |

---

## CPS Score (ChatDT Performance Score)

Metrica propietaria que evalua el rendimiento real de un equipo:

```
CPS = Threat + Control + Friction

Threat   = (Tiros al arco * 3) + (Tiros dentro del area * 2) + Corners - (Offsides * 0.3)
Control  = (Posesion% * 40) + (Precision pases% * 50) + (Total pases * 0.02)
Friction = (Faltas * -0.5) + (Amarillas * -3) + (Rojas * -10)
```

**Interpretacion:**
- CPS > 80: Rendimiento excelente
- CPS 60-80: Rendimiento solido
- CPS < 60: Rendimiento deficiente

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/ChatDT.git
cd ChatDT
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia `.env.example` a `.env` y completa tus API keys:

```bash
cp .env.example .env
```

```env
# API-FOOTBALL (datos de partidos)
# Obtener en: https://dashboard.api-football.com
API_FOOTBALL_KEY=tu_api_key

# Liga Argentina
LEAGUE_ID=128
SEASON=2023

# LLM (100% GRATIS)
# Obtener en: https://console.groq.com/keys
LLM_PROVIDER=groq
GROQ_API_KEY=tu_groq_key
```

---

## Uso

### Opcion 1: Frontend Web (Recomendado)

```bash
streamlit run app.py
```

Abre http://localhost:8501 en tu navegador. Interfaz estilo "War Room" con:
- Selector de partidos y equipos
- Visualizacion de CPS Score en tiempo real
- Graficos tacticos interactivos
- Cronicas generadas por IA

### Opcion 2: Linea de Comandos

```bash
# Analizar por ID de partido
python main.py --fixture 971362

# Analizar ultimo partido de un equipo
python main.py --team 451  # Boca Juniors
```

### Output

El sistema genera:

```
data/
  reports/
    report_971362.md        # Cronica periodistica
  visualizations/
    match_analysis_971362.png  # Graficos
  processed/
    analysis_971362.json    # Datos procesados
```

---

## Estructura del Proyecto

```
ChatDT/
|-- main.py           # Orquestador LangGraph (Fase 5)
|-- scout.py          # Agente de ingesta de datos (Fase 2)
|-- analyst.py        # Agente de analisis CPS (Fase 3)
|-- visualizer.py     # Agente de visualizacion (Fase 4)
|-- config_check.py   # Verificacion de configuracion (Fase 1)
|
|-- data/
|   |-- raw/          # JSONs crudos de API-FOOTBALL
|   |-- processed/    # Analisis procesados
|   |-- reports/      # Cronicas en Markdown
|   |-- visualizations/  # Graficos PNG
|
|-- examples/         # Ejemplos de output
|-- requirements.txt  # Dependencias
|-- .env.example      # Template de configuracion
```

---

## APIs y Limites

### API-FOOTBALL (Plan Gratuito)

| Limite | Valor |
|--------|-------|
| Requests/dia | 100 |
| Requests/min | 10 |
| Temporadas | 2021-2023 |

**Optimizacion:** El sistema usa cache local para minimizar llamadas.

### LLM - Groq (Gratuito)

| Limite | Valor |
|--------|-------|
| Requests/min | 30 |
| Requests/dia | 14,400 |
| Modelo | Llama 3.3 70B |

---

## Tech Stack

| Categoria | Tecnologia |
|-----------|------------|
| Lenguaje | Python 3.11+ |
| Orquestacion | LangGraph |
| Datos | API-FOOTBALL |
| LLM | Groq (Llama 3.3) / Gemini |
| Visualizacion | mplsoccer, matplotlib |
| Data Processing | Pandas, NumPy |

---

## Ejemplos de Output

### Visualizacion Tactica

El sistema genera un grafico combinado con:
- Formaciones tacticas de ambos equipos
- Radar chart comparativo de metricas

### Cronica Periodistica

```markdown
# El Xeneize se impone en la Bombonera

El **Boca Juniors** se llevo los tres puntos en un partido intenso 
contra **Atletico Tucuman**. La victoria de 1-0 refleja la superioridad 
numerica: un CPS de 103.8 frente a 60.0...
```

---

## Roadmap

- [x] Fase 1: Configuracion y conexion a API
- [x] Fase 2: Scout Agent (ingesta de datos)
- [x] Fase 3: Analyst Agent (CPS Score)
- [x] Fase 4: Visualizer Agent (graficos)
- [x] Fase 5: Writer Agent (LangGraph + LLM)
- [x] Fase 6: Documentacion y portafolio
- [ ] Fase 7: Interfaz web (Streamlit)
- [ ] Fase 8: Analisis en tiempo real

---

## Autor

**Gonzalo Pontnau**

- GitHub: [@gonzalopontnau](https://github.com/gonzalopontnau)
- LinkedIn: [Gonzalo Pontnau](https://linkedin.com/in/gonzalopontnau)

---

## Licencia

MIT License - Ver [LICENSE](LICENSE) para mas detalles.

---

*Built with Python, LangGraph, and passion for football.*
