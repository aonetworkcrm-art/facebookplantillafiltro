"""
affiliate-ai-agent/agent/content_planner.py
80/20 Content Planner.
Implements the strategy: 80% value content, 20% promotional content.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
import json
import os
import random

from .database import Database


@dataclass
class ContentIdea:
    """A generated content idea."""
    title: str
    content_type: str  # "value" or "promotion"
    category: str  # e.g., "tip", "tutorial", "caso_estudio", "review"
    description: str
    target_group: str = ""
    scheduled_date: str = ""
    posted: bool = False
    engagement_result: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ContentIdea":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ContentPlanner:
    """
    Planning engine that enforces the 80/20 rule.
    Generates content ideas and schedules.
    """

    # Templates for value content (80%)
    VALUE_TEMPLATES = [
        "5 {niche} tips que {dolor}",
        "Cómo {beneficio} sin {obstaculo}",
        "El error #1 que cometen los principiantes en {niche}",
        "{numero} señales de que necesitas {solucion}",
        "La verdad sobre {tema} que nadie te cuenta",
        "Cómo {logro} en solo {tiempo}",
        "Lo que aprendí después de {experiencia} en {niche}",
        "{herramienta} vs {herramienta2}: ¿cuál es mejor para {objetivo}?",
        "Mitología vs Realidad: {mito} en {niche}",
        "Paso a paso: cómo {proceso} desde cero",
    ]

    # Templates for promotional content (20%)
    PROMO_TEMPLATES = [
        "Mi experiencia con {producto}: ¿realmente funciona?",
        "Hice {accion} y esto pasó (resultados reales)",
        "Si estás listo para {beneficio}, esto es para ti",
        "Lo que incluye {producto} y por qué me decidí",
        "Oferta especial: {producto} con {bono} incluido",
        "¿Vale la pena {producto}? Te cuento mi experiencia honesta",
    ]

    # Value content categories
    VALUE_CATEGORIES = [
        "tip", "tutorial", "caso_estudio", "tendencia",
        "mitos_vs_realidad", "preguntas_frecuentes", "herramientas",
        "errores_comunes", "inspiracion", "guia"
    ]

    # Promo content categories
    PROMO_CATEGORIES = [
        "review", "testimonio", "oferta", "comparativa",
        "resultados", "caso_exito"
    ]

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db = Database(data_dir)
        self._ideas: list[ContentIdea] = []
        self._load()

    def _load(self) -> None:
        data = self.db.load_content_ideas()
        self._ideas = [ContentIdea.from_dict(d) for d in data]

    def _save(self) -> None:
        self.db.save_content_ideas([i.to_dict() for i in self._ideas])

    @property
    def ideas(self) -> list[ContentIdea]:
        return self._ideas

    def generate_ideas(self, niche: str, count: int = 10) -> list[ContentIdea]:
        """
        Generate content ideas respecting the 80/20 rule.
        For every 10 ideas: 8 value, 2 promotional.
        """
        value_count = int(count * 0.8)
        promo_count = count - value_count

        vars = {
            "niche": niche,
            "dolor": random.choice([
                "realmente funcionan", "te ayudarán hoy",
                "marcan la diferencia"
            ]),
            "beneficio": random.choice([
                "lograr resultados", "ahorrar tiempo", "aumentar ventas",
                "mejorar tus habilidades"
            ]),
            "obstaculo": random.choice([
                "complicarte", "gastar dinero", "experiencia previa",
                "tener seguidores"
            ]),
            "numero": random.choice(["3", "5", "7", "10"]),
            "solucion": random.choice([
                "esta solución", "mejorar", "un cambio"
            ]),
            "tema": random.choice([
                niche, f"el {niche} moderno", niche
            ]),
            "logro": random.choice([
                "empezar desde cero", "generar tus primeras ventas",
                "conseguir clientes"
            ]),
            "tiempo": random.choice([
                "30 días", "una semana", "poco tiempo"
            ]),
            "experiencia": random.choice([
                "mis inicios", "fracasar", "años trabajando",
            ]),
            "herramienta": random.choice([
                "Herramienta A", "Método tradicional", "Enfoque antiguo"
            ]),
            "herramienta2": random.choice([
                "Herramienta B", "Nuevo método", "Enfoque moderno"
            ]),
            "objetivo": random.choice([
                "principiantes", "avanzados", "todos"
            ]),
            "mito": random.choice([
                "más seguidores = más ventas",
                "necesitas invertir mucho dinero",
                "solo funciona para ciertos nichos"
            ]),
            "proceso": random.choice([
                "empezar en " + niche,
                "crear tu primer proyecto",
                "generar ingresos con " + niche
            ]),
            "producto": "[Tu Producto]",
            "accion": random.choice([
                "la prueba durante 30 días",
                "aplicé el método al pie de la letra"
            ]),
            "bono": "[Bono Exclusivo]",
        }

        ideas = []

        # Generate value content
        for _ in range(value_count):
            template = random.choice(self.VALUE_TEMPLATES)
            title = self._fill_template(template, vars)
            ideas.append(ContentIdea(
                title=title,
                content_type="value",
                category=random.choice(self.VALUE_CATEGORIES),
                description="Contenido educativo para construir autoridad."
            ))

        # Generate promotional content
        for _ in range(promo_count):
            template = random.choice(self.PROMO_TEMPLATES)
            title = self._fill_template(template, vars)
            ideas.append(ContentIdea(
                title=title,
                content_type="promotion",
                category=random.choice(self.PROMO_CATEGORIES),
                description="Contenido promocional con llamado a la acción."
            ))

        random.shuffle(ideas)
        self._ideas.extend(ideas)
        self._save()
        return ideas

    def _fill_template(self, template: str, vars: dict) -> str:
        """Fill a template with variables, handling missing keys gracefully.
        Uses the niche name as fallback for unfilled placeholders.
        """
        result = template
        for key, value in vars.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value)
        # Replace any remaining unfilled placeholders with a graceful fallback
        while "{" in result and "}" in result:
            start = result.find("{")
            end = result.find("}") + 1
            placeholder_name = result[start+1:end-1]
            if placeholder_name in vars:
                fallback = vars[placeholder_name]
            elif placeholder_name == "niche":
                fallback = vars.get("niche", "tu nicho")
            else:
                fallback = "este tema"
            result = result[:start] + fallback + result[end:]
        return result

    def schedule_week(self, start_date: str = "") -> list[ContentIdea]:
        """Schedule ideas for an entire week respecting 80/20."""
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        start = datetime.strptime(start_date, "%Y-%m-%d")
        scheduled = []

        # We need at least some ideas to schedule
        if len(self._ideas) < 7:
            return []

        value_ideas = [i for i in self._ideas if i.content_type == "value"
                       and not i.scheduled_date]
        promo_ideas = [i for i in self._ideas if i.content_type == "promotion"
                       and not i.scheduled_date]

        # 6 value days + 1 promo day (roughly 80/20)
        for day_offset in range(7):
            day = start + timedelta(days=day_offset)
            date_str = day.strftime("%Y-%m-%d")
            day_name = day.strftime("%A")

            # Sunday is promotion day (20%)
            is_promo = day_name.lower() in ["sunday", "domingo"] and promo_ideas

            if is_promo and promo_ideas:
                idea = promo_ideas.pop(0)
            elif value_ideas:
                idea = value_ideas.pop(0)
            else:
                continue

            idea.scheduled_date = date_str
            self._save()
            scheduled.append(idea)

        return scheduled

    def get_stats(self) -> dict:
        """Get 80/20 compliance statistics."""
        total = len(self._ideas)
        if total == 0:
            return {"total": 0, "value": 0, "promotion": 0,
                    "ratio": 0, "target_ratio": 0.8, "compliant": False}

        value = sum(1 for i in self._ideas if i.content_type == "value")
        promotion = sum(1 for i in self._ideas if i.content_type == "promotion")
        posted = sum(1 for i in self._ideas if i.posted)
        ratio = value / total if total > 0 else 0

        return {
            "total": total,
            "value": value,
            "promotion": promotion,
            "ratio": round(ratio, 2),
            "target_ratio": 0.8,
            "compliant": ratio >= 0.8,
            "posted": posted,
            "scheduled": sum(1 for i in self._ideas
                             if i.scheduled_date and not i.posted)
        }

    def mark_posted(self, title: str, engagement: str = "") -> bool:
        """Mark an idea as posted."""
        for idea in self._ideas:
            if idea.title == title and not idea.posted:
                idea.posted = True
                idea.engagement_result = engagement
                self._save()
                return True
        return False

    def get_weekly_calendar(self) -> dict:
        """Get a formatted weekly calendar of scheduled content."""
        days = ["Lunes", "Martes", "Miércoles", "Jueves",
                "Viernes", "Sábado", "Domingo"]
        calendar = {}
        for day in days:
            calendar[day] = []

        for idea in self._ideas:
            if idea.scheduled_date:
                dt = datetime.strptime(idea.scheduled_date, "%Y-%m-%d")
                day_name = dt.strftime("%A").lower()
                day_es = {
                    "monday": "Lunes", "tuesday": "Martes",
                    "wednesday": "Miércoles", "thursday": "Jueves",
                    "friday": "Viernes", "saturday": "Sábado",
                    "sunday": "Domingo"
                }.get(day_name, "Lunes")

                if day_es in calendar:
                    calendar[day_es].append(idea)

        return calendar
