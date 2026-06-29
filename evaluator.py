import re
from typing import List

# Scoring thresholds → nivel
def _score_to_nivel(score: int) -> str:
    if score >= 90:
        return "Experto"
    elif score >= 75:
        return "Avanzado"
    elif score >= 60:
        return "Competente"
    elif score >= 40:
        return "En desarrollo"
    else:
        return "Principiante"


# Per-scenario keyword sets: one list of keywords per criterion
CRITERIA_KEYWORDS = {
    1: [  # RRHH - Absentismo
        ["dax", "medida", "días ausentes", "dias ausentes", "días laborables", "dias laborables",
         "porcentaje", "calcul", "fórmula", "formula", "divide", "absentismo", "%"],
        ["filtro", "departamento", "tipo de ausencia", "período", "periodo",
         "segmentador", "slicer", "mes", "año", "fecha"],
        ["gráfico", "grafico", "visual", "línea", "linea", "barras", "barra",
         "chart", "tabla", "visualización", "visualizacion"],
        ["ausencias", "empleados", "tabla", "relación", "relacion", "columna",
         "campo", "id_empleado", "tablas"],
        ["necesito", "quiero", "crea", "diseña", "disena", "calcula", "muestra",
         "objetivo", "informe", "crear", "diseñar"],
    ],
    2: [  # Ventas - Cumplimiento
        ["cumplimiento", "dax", "medida", "porcentaje", "real vs objetivo", "objetivo",
         "calcul", "% cumplimiento", "real", "ventas real"],
        ["kpi", "semáforo", "semaforo", "formato condicional", "condicional",
         "color", "indicador", "verde", "rojo", "visual"],
        ["ytd", "acumulado", "año", "anual", "acumulado anual", "totalytd", "year to date"],
        ["filtro", "segmentador", "slicer", "región", "region", "comercial", "período", "periodo"],
        ["dashboard", "visual", "gráfico", "grafico", "resultado", "ver", "muestra",
         "informe", "diseña", "crea"],
    ],
    3: [  # Finanzas - Variación costes
        ["desviación", "desviacion", "real - presupuesto", "fórmula", "formula",
         "absoluto", "porcentaje", "calcul", "dax", "variación", "variacion"],
        ["favorable", "desfavorable", "color", "formato condicional", "indicador",
         "semáforo", "semaforo", "verde", "rojo"],
        ["relacion", "relación", "centro de coste", "categoría", "categoria",
         "join", "unir", "tabla", "tablas", "relacionar"],
        ["waterfall", "tabla", "visual", "gráfico", "grafico", "condicional",
         "barras", "chart", "cascade"],
        ["medida", "métrica", "metrica", "contexto", "especifica", "necesito",
         "quiero", "ambas", "métrica"],
    ],
    4: [  # Logística - Tiempo entrega
        ["datediff", "dax", "calcul", "tiempo de entrega", "horas", "días", "dias",
         "diferencia", "fecha_pedido", "fecha_entrega", "plazo", "entrega"],
        ["sla", "incumplimiento", "comprometido", "comparar", "supera", "excede",
         "48h", "72h", "horas comprometidas"],
        ["filtro", "zona", "transportista", "período", "periodo", "estado", "segmentador"],
        ["mapa", "tabla", "visual", "gráfico", "grafico", "barras", "chart",
         "problemática", "problematica", "zonas"],
        ["medir", "medida", "objetivo", "específico", "especifico", "necesito",
         "quiero", "calcular", "crea", "diseña"],
    ],
    5: [  # Marketing - ROI
        ["roi", "ingresos", "inversión", "inversion", "fórmula", "formula",
         "calcul", "retorno", "rentabilidad", "return"],
        ["coste por lead", "cpl", "lead", "coste", "costo", "leads generados", "nº de leads"],
        ["campañas", "campanas", "leads", "ventas_lead", "relación", "relacion",
         "tabla", "tablas", "relacionar"],
        ["canal", "google ads", "redes sociales", "email", "segmentador", "filtro",
         "período", "periodo"],
        ["ranking", "comparativa", "visual", "gráfico", "grafico", "dashboard",
         "output", "resultado", "ver", "muestra"],
    ],
}

# Feedback when criterion is NOT met
CRITERIA_NEGATIVE_FEEDBACK = {
    1: [
        "Incluye la fórmula DAX para calcular el % de absentismo: Días_Ausencia / Días_Laborables * 100",
        "Especifica los filtros requeridos: departamento, tipo de ausencia y período temporal",
        "Indica el tipo de visual adecuado: gráfico de líneas para tendencia o barras para comparativa",
        "Menciona las tablas Ausencias y Empleados y la relación entre ellas por ID_Empleado",
        "Usa verbos concretos (crea, diseña, calcula) para que el prompt sea claro y accionable",
    ],
    2: [
        "Define la medida DAX de cumplimiento: DIVIDE([Ventas Real], [Objetivo Mensual]) * 100",
        "Menciona formato condicional o visual KPI para mostrar semáforos (verde/rojo)",
        "Indica cómo calcular el acumulado YTD con TOTALYTD frente al objetivo anual",
        "Especifica segmentadores por región, comercial o período temporal",
        "Describe el resultado visual esperado: tabla de comerciales con indicadores de cumplimiento",
    ],
    3: [
        "Define la fórmula: Desviación = Importe_Real - Importe_Presupuestado; % = Desviación/Presupuesto*100",
        "Indica cómo representar si la desviación es favorable o desfavorable (colores, semáforo)",
        "Menciona que hay que relacionar Gastos y Presupuesto por Centro_Coste + Categoría + período",
        "Propone un visual adecuado: tabla con formato condicional o gráfico waterfall",
        "Especifica tanto la métrica de desviación como el contexto visual esperado",
    ],
    4: [
        "Propone DATEDIFF en DAX para calcular días/horas entre Fecha_Pedido y Fecha_Entrega",
        "Menciona la comparativa con la tabla SLA y la identificación de incumplimientos",
        "Indica los filtros útiles: zona geográfica, transportista, período y estado del pedido",
        "Propone un visual para identificar zonas problemáticas: mapa, barras o tabla",
        "Sé más específico sobre qué medir (tiempo medio de entrega) y cómo visualizarlo",
    ],
    5: [
        "Define la fórmula ROI: (Ingresos - Inversión) / Inversión * 100",
        "Propone el cálculo de coste por lead: Inversión / Número de Leads generados",
        "Indica las relaciones entre tablas: Campañas → Leads → Ventas_Lead",
        "Menciona segmentadores por canal (Google Ads, Redes Sociales, Email) y período",
        "Describe el output visual esperado: ranking de campañas por ROI o comparativa por canal",
    ],
}

# Feedback when criterion IS met
CRITERIA_POSITIVE_FEEDBACK = {
    1: [
        "Incluye el cálculo DAX o referencia a la fórmula de absentismo",
        "Especifica correctamente los filtros necesarios para el análisis",
        "Indica el tipo de visual adecuado para la situación",
        "Proporciona contexto sobre las tablas o relaciones del modelo",
        "El prompt es claro, concreto y accionable",
    ],
    2: [
        "Propone una medida DAX para calcular el cumplimiento",
        "Menciona indicadores visuales o formato condicional para semáforos",
        "Contempla el análisis acumulado YTD frente al objetivo anual",
        "Especifica los filtros o segmentadores necesarios",
        "Describe con claridad el resultado visual esperado",
    ],
    3: [
        "Define la fórmula de desviación de costes",
        "Indica cómo representar visualmente si la desviación es favorable o no",
        "Menciona la relación necesaria entre las tablas de Gastos y Presupuesto",
        "Propone un tipo de visual adecuado para la variación de costes",
        "Especifica tanto la métrica como el contexto visual",
    ],
    4: [
        "Propone el cálculo del tiempo de entrega en DAX",
        "Contempla la comparativa con el SLA y la detección de incumplimientos",
        "Especifica los filtros necesarios para el análisis logístico",
        "Propone un visual adecuado para identificar zonas problemáticas",
        "El prompt es específico sobre qué medir y cómo visualizarlo",
    ],
    5: [
        "Define la fórmula de ROI correctamente",
        "Propone el cálculo del coste por lead",
        "Indica las relaciones necesarias entre las tablas",
        "Menciona segmentadores por canal y período",
        "Describe el output visual esperado para la comparativa de campañas",
    ],
}

# Curated improved prompt examples per scenario
IMPROVED_PROMPTS = {
    1: (
        "Necesito crear una medida DAX que calcule el porcentaje de absentismo mensual: "
        "% Absentismo = DIVIDE(SUM(Ausencias[Dias_Ausencia]), [Días_Laborables]) * 100. "
        "Visualízalo en un gráfico de líneas con el mes en el eje X y el % de absentismo en el eje Y. "
        "Añade segmentadores para filtrar por Departamento y Tipo_Ausencia. "
        "Las tablas Ausencias y Empleados están relacionadas por ID_Empleado."
    ),
    2: (
        "Crea una medida DAX: % Cumplimiento = DIVIDE([Ventas Real], [Objetivo Mensual]) * 100. "
        "Diseña una tabla con formato condicional: verde ≥100 %, amarillo 80–99 %, rojo <80 %. "
        "Añade una tarjeta KPI con el acumulado YTD usando TOTALYTD comparado con el objetivo anual. "
        "Incluye segmentadores por Región y período. Las tablas son Ventas, Comerciales y Objetivos."
    ),
    3: (
        "Necesito dos medidas DAX: "
        "Desviación Absoluta = [Importe Real] - [Importe Presupuestado] y "
        "% Desviación = DIVIDE([Desviación Absoluta], [Importe Presupuestado]) * 100. "
        "Muéstralas en una tabla con formato condicional: rojo si desfavorable, verde si favorable. "
        "Las tablas Gastos y Presupuesto deben relacionarse por Centro_Coste + Categoría + período."
    ),
    4: (
        "Calcula el tiempo medio de entrega en DAX: "
        "Tiempo Entrega (días) = AVERAGEX(Pedidos, DATEDIFF(Pedidos[Fecha_Pedido], Pedidos[Fecha_Entrega], DAY)). "
        "Compara con la tabla SLA por Zona y crea un indicador de incumplimiento. "
        "Visualiza en un gráfico de barras por Zona y Transportista. "
        "Añade filtros por Zona, Transportista y Estado del pedido."
    ),
    5: (
        "Crea estas medidas DAX: "
        "ROI = DIVIDE([Ingresos Leads] - SUM(Campañas[Inversión]), SUM(Campañas[Inversión])) * 100 y "
        "Coste por Lead = DIVIDE(SUM(Campañas[Inversión]), COUNTROWS(Leads)). "
        "Las tablas se relacionan: Campañas → Leads → Ventas_Lead. "
        "Diseña un ranking de campañas por ROI y un gráfico comparativo por Canal. "
        "Añade segmentadores por Canal y período temporal."
    ),
}


_STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "por", "para", "con",
    "una", "un", "que", "se", "es", "del", "al", "o", "si", "entre", "como",
    "su", "sus", "lo", "le", "les", "nos", "más", "son", "tiene", "hay",
    "tanto", "ambas", "cada", "este", "esta", "estos", "estas", "también",
}

def _word_set(text: str) -> set:
    words = re.findall(r"[a-záéíóúüñ]+", text.lower())
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}

def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def _is_copied(student_prompt: str, example: str, threshold: float = 0.55) -> bool:
    return _jaccard(_word_set(student_prompt), _word_set(example)) >= threshold


def _matches(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def evaluate_prompt(scenario: dict, student_prompt: str) -> dict:
    scenario_id = scenario["id"]

    if (_is_copied(student_prompt, IMPROVED_PROMPTS[scenario_id])
            or _is_copied(student_prompt, scenario["goal"], threshold=0.45)):
        return {
            "puntuacion_total": 0,
            "nivel": "Principiante",
            "criterios": [
                {"nombre": c, "cumplido": False, "comentario": "Evaluación anulada por copia del prompt de ejemplo."}
                for c in scenario["criteria"]
            ],
            "fortalezas": [],
            "mejoras": ["El prompt enviado coincide con el ejemplo o con el enunciado del ejercicio. Escribe tu propia solución con tus propias palabras."],
            "ejemplo_prompt_mejorado": IMPROVED_PROMPTS[scenario_id],
        }

    criteria = scenario["criteria"]
    kw_sets = CRITERIA_KEYWORDS[scenario_id]
    pos_fb = CRITERIA_POSITIVE_FEEDBACK[scenario_id]
    neg_fb = CRITERIA_NEGATIVE_FEEDBACK[scenario_id]

    word_count = len(student_prompt.split())
    results = []
    cumplidos = 0

    for i, criterion in enumerate(criteria):
        met = _matches(student_prompt, kw_sets[i])
        # Last criterion (clarity): also accept prompts with ≥40 words
        if i == len(criteria) - 1:
            met = met or word_count >= 40

        if met:
            cumplidos += 1

        results.append({
            "nombre": criterion,
            "cumplido": met,
            "comentario": pos_fb[i] if met else neg_fb[i],
        })

    points_per_criterion = 100 // len(criteria)
    score = cumplidos * points_per_criterion
    if word_count >= 60 and score < 100:
        score = min(score + 5, 100)

    nivel = _score_to_nivel(score)

    fortalezas = [pos_fb[i] for i, r in enumerate(results) if r["cumplido"]]
    if not fortalezas:
        fortalezas = ["Has intentado responder a la situación planteada"]

    mejoras = [neg_fb[i] for i, r in enumerate(results) if not r["cumplido"]]
    if not mejoras:
        mejoras = ["¡Excelente trabajo! Revisa los detalles técnicos para alcanzar nivel Experto"]

    return {
        "puntuacion_total": score,
        "nivel": nivel,
        "criterios": results,
        "fortalezas": fortalezas[:3],
        "mejoras": mejoras[:3],
        "ejemplo_prompt_mejorado": IMPROVED_PROMPTS[scenario_id],
    }


NIVEL_COLOR = {
    "Principiante": "#e74c3c",
    "En desarrollo": "#e67e22",
    "Competente": "#f1c40f",
    "Avanzado": "#2ecc71",
    "Experto": "#27ae60",
}

NIVEL_EMOJI = {
    "Principiante": "🔴",
    "En desarrollo": "🟠",
    "Competente": "🟡",
    "Avanzado": "🟢",
    "Experto": "🌟",
}
