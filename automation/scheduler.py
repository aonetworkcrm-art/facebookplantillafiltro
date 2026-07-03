"""
affiliate-ai-agent/automation/scheduler.py
Content Scheduler - Automates the daily posting routine.
Implements the "mañana, tarde y noche" strategy from the video.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Ensure the project root is on sys.path for direct execution
try:
    from agent.strategy import StrategyEngine
    from agent.database import Database
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from agent.strategy import StrategyEngine
    from agent.database import Database


class RoutineScheduler:
    """
    Automates the daily 3-times routine from the strategy:
    - Mañana: Publicar contenido de valor
    - Tarde: Interactuar y responder
    - Noche: Revisar métricas y planificar
    """

    ROUTINE = {
        "morning": {
            "time": "07:00 - 09:00",
            "title": "🌅 Mañana — Publicar contenido de valor",
            "tasks": [
                "Publica 1 contenido de valor en 3-5 grupos activos",
                "Comparte un tip rápido o reflexión",
                "Revisa notificaciones de la noche anterior"
            ]
        },
        "afternoon": {
            "time": "12:00 - 14:00",
            "title": "☀️ Tarde — Interacción y seguimiento",
            "tasks": [
                "Responde comentarios en tus publicaciones",
                "Interactúa en publicaciones de otros miembros",
                "Da seguimiento a leads interesados por WhatsApp"
            ]
        },
        "evening": {
            "time": "19:00 - 21:00",
            "title": "🌙 Noche — Revisión y planificación",
            "tasks": [
                "Revisa métricas del día (engagement, leads, ventas)",
                "Prepara el contenido para mañana",
                "Registra nuevos leads y actualiza estados"
            ]
        }
    }

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
        self.data_dir = data_dir
        self.db = Database(data_dir)
        self.engine = StrategyEngine(data_dir)
        self.today = datetime.now()

    def get_routine_for_time(self) -> dict:
        """Get the routine task for the current time of day."""
        hour = self.today.hour
        if 7 <= hour < 12:
            return self.ROUTINE["morning"]
        elif 12 <= hour < 19:
            return self.ROUTINE["afternoon"]
        else:
            return self.ROUTINE["evening"]

    def get_today_plan(self) -> dict:
        """Get a complete plan for today."""
        day_name = self.today.strftime("%A")
        days_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
            "Thursday": "Jueves", "Friday": "Viernes",
            "Saturday": "Sábado", "Sunday": "Domingo"
        }

        active_groups = []
        try:
            from agent.group_finder import GroupFinder
            gf = GroupFinder(self.data_dir)
            for g in gf.get_active_groups():
                active_groups.append(g.name)
        except Exception:
            pass

        return {
            "date": self.today.strftime("%Y-%m-%d"),
            "day": days_es.get(day_name, day_name),
            "routines": [
                {
                    "period": period,
                    "title": data["title"],
                    "tasks": data["tasks"]
                }
                for period, data in self.ROUTINE.items()
            ],
            "active_groups": active_groups,
            "stats": {
                "campaigns": len(self.engine.campaigns),
                "niche": self.engine.config.niche
            }
        }

    def generate_daily_report(self) -> str:
        """Generate a formatted daily report."""
        plan = self.get_today_plan()
        groups_info = (
            f"Grupos activos: {', '.join(plan['active_groups']) or 'Ninguno aún'}"
        )

        lines = [
            f"\n╔═══ 📋 PLAN DEL DÍA — {plan['day']} {plan['date']} ═══╗\n",
            f"📌 Nicho: {plan['stats']['niche'] or 'No configurado'}",
            f"📦 Campañas: {plan['stats']['campaigns']}",
            groups_info,
            "\n─── RUTINA DIARIA ───"
        ]
        for r in plan["routines"]:
            lines.append(f"\n{r['title']}:")
            for task in r["tasks"]:
                lines.append(f"  ☐ {task}")

        lines.append("\n💡 Tip del día: " + self._get_daily_tip())
        lines.append("═" * 45)
        return "\n".join(lines)

    def _get_daily_tip(self) -> str:
        """Get a random daily tip."""
        try:
            from agent.knowledge_base import KnowledgeBase
        except ImportError:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from agent.knowledge_base import KnowledgeBase
        return KnowledgeBase.get_random_tip("general")

    def get_weekly_plan(self) -> list[dict]:
        """Get a plan for the entire week."""
        week_plan = []
        for day_offset in range(7):
            day = self.today + timedelta(days=day_offset)
            days_es = {
                "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                "Thursday": "Jueves", "Friday": "Viernes",
                "Saturday": "Sábado", "Sunday": "Domingo"
            }
            # Sunday = promotion day
            is_promo = day.strftime("%A") in ("Sunday",)
            week_plan.append({
                "date": day.strftime("%Y-%m-%d"),
                "day": days_es.get(day.strftime("%A"), day.strftime("%A")),
                "focus": "🛒 Promoción" if is_promo else "📚 Valor",
                "description": (
                    "Enfócate en contenido promocional con llamado a la acción"
                    if is_promo else
                    "Publica contenido educativo y construye autoridad"
                )
            })
        return week_plan

    def save_routine_log(self, period: str, completed: list[str]) -> None:
        """Log completed tasks for a period."""
        date_str = self.today.strftime("%Y-%m-%d")
        self.db.save_routine_entry(
            date_str, period, datetime.now().isoformat(), completed
        )


def main():
    """CLI entry point for the scheduler."""
    import argparse
    parser = argparse.ArgumentParser(description="Planificador diario de rutina")
    parser.add_argument("--today", action="store_true", help="Ver plan del día")
    parser.add_argument("--week", action="store_true", help="Ver plan semanal")
    parser.add_argument("--report", action="store_true", help="Generar reporte diario")
    args = parser.parse_args()

    scheduler = RoutineScheduler()

    if args.today:
        plan = scheduler.get_today_plan()
        print(f"\n📋 Plan para {plan['day']} {plan['date']}:")
        for r in plan["routines"]:
            print(f"\n{r['title']}:")
            for task in r["tasks"]:
                print(f"  ☐ {task}")

    if args.week:
        print("\n📅 Plan Semanal:")
        for day in scheduler.get_weekly_plan():
            print(f"\n{day['day']} {day['date']} — {day['focus']}")
            print(f"  {day['description']}")

    if args.report:
        print(scheduler.generate_daily_report())

    if not any([args.today, args.week, args.report]):
        print(scheduler.generate_daily_report())


if __name__ == "__main__":
    main()
