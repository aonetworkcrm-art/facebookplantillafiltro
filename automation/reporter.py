"""
affiliate-ai-agent/automation/reporter.py
Campaign Reporter - Generates analytics and progress reports.
Helps track the key metrics from the strategy.
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional

# Ensure the project root is on sys.path for direct execution
try:
    from agent.strategy import StrategyEngine
    from agent.knowledge_base import KnowledgeBase
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from agent.strategy import StrategyEngine
    from agent.knowledge_base import KnowledgeBase


class CampaignReporter:
    """
    Generates detailed reports on campaign performance.
    Tracks the 6 key metrics from the Knowledge Base:
    1. Posts por día
    2. Comentarios por post
    3. Leads por WhatsApp por día
    4. Tasa de cierre
    5. Grupos activos
    6. Ingresos semanales
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
        self.data_dir = data_dir
        self.engine = StrategyEngine(data_dir)

    def generate_weekly_report(self, campaign_name: str) -> dict:
        """Generate a comprehensive weekly report."""
        report = self.engine.export_campaign_report(campaign_name)
        if "error" in report:
            return report

        # Add calculated metrics
        leads = report.get("leads", {})
        total_leads = leads.get("total", 0)
        closed = leads.get("closed", 0)

        report["calculated_metrics"] = {
            "close_rate": round(closed / total_leads * 100, 1) if total_leads > 0 else 0,
            "leads_per_day": round(total_leads / 7, 1) if total_leads > 0 else 0,
            "conversion_efficiency": self._calculate_efficiency(report),
            "weekly_progress": report.get("current_sales", 0) - 0  # simplified
        }

        return report

    def _calculate_efficiency(self, report: dict) -> str:
        """Calculate overall efficiency rating."""
        groups = report.get("groups", {})
        content = report.get("content", {})

        score = 0
        if groups.get("allowed", 0) >= 5:
            score += 1
        if groups.get("allowed", 0) >= 10:
            score += 1
        if content.get("compliant"):
            score += 1
        if content.get("posted", 0) >= 10:
            score += 1
        if report.get("current_sales", 0) > 0:
            score += 1
        if report.get("current_sales", 0) >= 5:
            score += 1

        if score >= 5:
            return "🔥 Excelente"
        elif score >= 3:
            return "👍 Buena"
        elif score >= 1:
            return "📈 En progreso"
        else:
            return "🚀 Recién empezando"

    def format_report_text(self, report: dict) -> str:
        """Format a report as readable text."""
        if "error" in report:
            return f"❌ Error: {report['error']}"

        metrics = report.get("calculated_metrics", {})
        content = report.get("content", {})
        leads = report.get("leads", {})
        groups = report.get("groups", {})

        return f"""
╔═══ 📊 REPORTE SEMANAL ═══╗

🎯 CAMPAÑA: {report.get('campaign', 'N/A')}
📦 Producto: {report.get('product', 'N/A')}
📌 Nicho: {report.get('niche', 'N/A')}
📊 Estado: {report.get('status', 'N/A')}

─── VENTAS ───
💰 Ventas: {report.get('current_sales', 0)} / {report.get('target_sales', 0)}
🎯 Progreso: {self._progress_bar(report.get('current_sales', 0), report.get('target_sales', 1))}

─── GRUPOS ───
🔍 Activos: {groups.get('allowed', 0)}
📝 Probados: {groups.get('allowed', 0) + groups.get('blocked', 0)}
⏳ Pendientes: {groups.get('untested', 0)}

─── CONTENIDO 80/20 ───
📚 Valor: {content.get('value', 0)} ({content.get('ratio', 0) * 100:.0f}%)
🛒 Promo: {content.get('promotion', 0)}
✅ Publicados: {content.get('posted', 0)}
{'✅ Ratio 80/20 CUMPLIDO' if content.get('compliant') else '⚠️ Ajusta tu ratio de contenido'}

─── LEADS ───
💬 Total: {leads.get('total', 0)}
🆕 Nuevos: {leads.get('new', 0)}
✅ Cerrados: {leads.get('closed', 0)}
📊 Tasa de cierre: {metrics.get('close_rate', 0)}%
💡 Leads/día: {metrics.get('leads_per_day', 0)}

─── EFICIENCIA ───
{metrics.get('conversion_efficiency', '🚀 Recién empezando')}

{'═' * 35}
📈 Sigue así. La constancia es la clave. 🚀
"""
    def _progress_bar(self, current: int, target: int, width: int = 20) -> str:
        """Generate a text-based progress bar."""
        if target <= 0:
            return "[" + "░" * width + "]"
        filled = int((current / target) * width)
        bar = "█" * min(filled, width) + "░" * (width - min(filled, width))
        return f"[{bar}] {current}/{target}"

    def generate_daily_summary(self) -> str:
        """Generate a quick daily summary."""
        active_campaigns = [c for c in self.engine.campaigns
                           if c.status == "active"]

        total_sales = sum(c.current_sales for c in self.engine.campaigns)
        total_target = sum(c.target_sales for c in self.engine.campaigns)

        # Count groups from group finder
        active_groups_count = 0
        try:
            from agent.group_finder import GroupFinder
            gf = GroupFinder(self.data_dir)
            active_groups_count = len(gf.get_active_groups())
        except Exception:
            pass

        # Count leads from lead tracker
        total_leads = 0
        closed_leads = 0
        try:
            from agent.lead_tracker import LeadTracker
            lt = LeadTracker(self.data_dir)
            total_leads = lt.get_pipeline_summary().get("total", 0)
            closed_leads = lt.get_pipeline_summary().get("closed", 0)
        except Exception:
            pass

        return f"""
╔═══ 📊 RESUMEN DIARIO — {datetime.now().strftime('%d/%m/%Y')} ═══╗

📦 Campañas activas: {len(active_campaigns)}
🔍 Grupos activos:    {active_groups_count}
💬 Leads totales:     {total_leads}
✅ Ventas cerradas:   {closed_leads}
💰 Progreso ventas:   {total_sales}/{total_target} {self._progress_bar(total_sales, total_target or 1)}

💡 "{KnowledgeBase.get_random_tip('general')}"

{'═' * 40}
"""
    def export_to_markdown(self, campaign_name: str) -> str:
        """Export report as Markdown."""
        import json
        report = self.generate_weekly_report(campaign_name)
        if "error" in report:
            return f"# Error\n\n{report['error']}"

        content = report.get("content", {})
        leads = report.get("leads", {})
        groups = report.get("groups", {})
        metrics = report.get("calculated_metrics", {})

        md = f"""# 📊 Reporte Semanal: {report.get('campaign', 'N/A')}

**Producto:** {report.get('product', 'N/A')}
**Nicho:** {report.get('niche', 'N/A')}
**Estado:** {report.get('status', 'N/A')}

## Ventas
- Progreso: {report.get('current_sales', 0)} / {report.get('target_sales', 0)}
- Eficiencia: {metrics.get('conversion_efficiency', 'N/A')}

## Grupos
| Métrica | Valor |
|---------|-------|
| Activos | {groups.get('allowed', 0)} |
| Probados | {groups.get('allowed', 0) + groups.get('blocked', 0)} |
| Pendientes | {groups.get('untested', 0)} |

## Contenido 80/20
| Tipo | Cantidad |
|------|----------|
| Valor | {content.get('value', 0)} ({content.get('ratio', 0) * 100:.0f}%) |
| Promoción | {content.get('promotion', 0)} |
| Publicados | {content.get('posted', 0)} |

## Leads
| Métrica | Valor |
|---------|-------|
| Totales | {leads.get('total', 0)} |
| Cerrados | {leads.get('closed', 0)} |
| Tasa de cierre | {metrics.get('close_rate', 0)}% |

---
*Generado: {datetime.now().isoformat()}*
"""
        return md


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Generador de reportes")
    parser.add_argument("--campaign", type=str, help="Nombre de la campaña")
    parser.add_argument("--daily", action="store_true", help="Resumen diario")
    parser.add_argument("--weekly", action="store_true", help="Reporte semanal")
    parser.add_argument("--markdown", action="store_true", help="Exportar como Markdown")
    args = parser.parse_args()

    reporter = CampaignReporter()

    if args.daily:
        print(reporter.generate_daily_summary())
        return

    if args.campaign:
        if args.markdown:
            print(reporter.export_to_markdown(args.campaign))
        elif args.weekly:
            report = reporter.generate_weekly_report(args.campaign)
            print(reporter.format_report_text(report))
        else:
            report = reporter.generate_weekly_report(args.campaign)
            print(reporter.format_report_text(report))
    else:
        print("Usa --campaign <nombre> o --daily para ver reportes.")


if __name__ == "__main__":
    main()
