# Ejemplos de Output - ChatDT

Este directorio contiene ejemplos reales generados por el sistema ChatDT.

## Partido Analizado

**Boca Juniors 1-0 Atletico Tucuman**
- Fecha: 2023-01-30
- Estadio: Estadio Alberto Jose Armando (La Bombonera)
- Fixture ID: 971362

---

## Archivos

### 1. Cronica Periodistica

`report_971362.md` - Cronica generada automaticamente por Llama 3.3 70B (Groq)

**Extracto:**
> "El Xeneize se impuso en la Bombonera con una victoria de 1-0. Con un CPS de 103.8 frente a 60.0, Boca demostro superioridad en control (75.1) y amenaza ofensiva (38.2)..."

### 2. Visualizacion Tactica

`match_analysis_971362.png` - Grafico combinado con:
- Formaciones tacticas de ambos equipos
- Radar chart comparativo de metricas clave

---

## CPS Score del Partido

| Metrica | Boca Juniors | Atletico Tucuman |
|---------|--------------|------------------|
| Threat | 38.2 | 28.6 |
| Control | 75.1 | 55.4 |
| Friction | -9.5 | -24.0 |
| **TOTAL** | **103.8** | **60.0** |

**Veredicto:** Boca gano y merecio el triunfo. Su CPS fue superior por 43.8 puntos.

---

## Como Reproducir

```bash
python main.py --fixture 971362
```

