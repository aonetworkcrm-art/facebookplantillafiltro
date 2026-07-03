"""
affiliate-ai-agent/agent/cli.py
Interactive CLI interface for the Affiliate AI Agent.
Uses rich for beautiful terminal output.
"""

import os
import sys
from datetime import datetime
from typing import Optional

# ─── Rich imports ────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.layout import Layout
    from rich.text import Text
    from rich.columns import Columns
    from rich.markdown import Markdown
    from rich import box
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback: simple print-based console
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def input(self, prompt=""):
            return input(prompt)

from .strategy import StrategyEngine, Campaign, Group, ContentItem, Lead
from .knowledge_base import KnowledgeBase
from .group_finder import GroupFinder
from .content_planner import ContentPlanner
from .lead_tracker import LeadTracker
from .campaign import CampaignManager
from automation.facebook_poster import FacebookPoster


class AffiliateCLI:
    """
    Interactive CLI agent that guides the user through the entire
    Hotmart Facebook Groups strategy.
    """

    BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🤖  AFILIADOS AI AGENT  🤖                                 ║
║   Tu asistente estratégico de marketing de afiliados        ║
║                                                              ║
║   Basado en la estrategia: Grupos de Facebook + Hotmart      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    def __init__(self):
        self.console = Console()
        self.data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize all modules
        self.strategy = StrategyEngine(self.data_dir)
        self.kb = KnowledgeBase()
        self.group_finder = GroupFinder(self.data_dir)
        self.content_planner = ContentPlanner(self.data_dir)
        self.lead_tracker = LeadTracker(self.data_dir)
        self.campaign_manager = CampaignManager(self.data_dir)
        self.facebook_poster = FacebookPoster(self.data_dir)

        self.current_campaign: Optional[Campaign] = None
        self.running = True

    # ─── Display Utilities ───────────────────────────────────────────────

    def _print(self, text: str, style: str = "default"):
        """Print styled text."""
        styles = {
            "title": "bold cyan",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
            "info": "blue",
            "highlight": "magenta",
            "default": "white"
        }
        s = styles.get(style, styles["default"])
        if RICH_AVAILABLE:
            self.console.print(text, style=s)
        else:
            print(text)

    def _panel(self, title: str, content: str, style: str = "cyan"):
        """Display content in a panel."""
        if RICH_AVAILABLE:
            self.console.print(Panel(content, title=title,
                                     border_style=style))
        else:
            self._print(f"\n--- {title} ---")
            self._print(content)

    def _table(self, title: str, columns: list, rows: list):
        """Display a table."""
        if RICH_AVAILABLE and rows:
            table = Table(title=title, box=box.ROUNDED)
            for col in columns:
                table.add_column(col, style="cyan")
            for row in rows:
                table.add_row(*[str(c) for c in row])
            self.console.print(table)
        else:
            self._print(f"\n{title}:")
            header = " | ".join(columns)
            self._print(header)
            self._print("-" * len(header))
            for row in rows:
                self._print(" | ".join(str(c) for c in row))

    def _menu(self, title: str, options: list) -> str:
        """Display a menu and get user choice."""
        self._print(f"\n[bold]{title}[/bold]" if RICH_AVAILABLE else f"\n{title}")
        for i, (key, desc) in enumerate(options, 1):
            self._print(f"  {key}. {desc}")
        choice = Prompt.ask("\nSelecciona una opción",
                            choices=[str(o[0]) for o in options],
                            default=str(options[0][0]))
        return choice

    def _input(self, prompt: str, default: str = "") -> str:
        """Get user input with optional default."""
        if default:
            return Prompt.ask(prompt, default=default)
        return Prompt.ask(prompt)

    def _confirm(self, prompt: str) -> bool:
        """Get a yes/no confirmation."""
        return Confirm.ask(prompt, default=True)

    def _clear(self):
        """Clear the screen."""
        os.system("cls" if os.name == "nt" else "clear")

    # ─── Main Loop ───────────────────────────────────────────────────────

    def run(self):
        """Main CLI loop."""
        self._clear()
        self._print(self.BANNER)

        if not self.strategy.is_configured():
            self._print("👋 ¡Bienvenido! Vamos a configurar tu estrategia de afiliados.\n",
                        "info")
            self._setup_wizard()

        while self.running:
            self._show_main_menu()

    def _show_main_menu(self):
        """Display the main menu."""
        self._print("\n" + "=" * 55)

        if self.current_campaign:
            self._print(f"📌 Campaña activa: [bold green]{self.current_campaign.name}[/bold green]"
                        if RICH_AVAILABLE else f"📌 Campaña activa: {self.current_campaign.name}")
        else:
            self._print("📌 Sin campaña activa")

        self._print("=" * 55)
        options = [
            ("1", "🎯  Estrategia - Ver los 6 pilares"),
            ("2", "📦  Campañas - Gestionar campañas"),
            ("3", "🔍  Grupos - Buscar y filtrar grupos"),
            ("4", "📊  Contenido - Planificador 80/20"),
            ("5", "💬  Leads - Gestión de leads WhatsApp"),
            ("6", "📈  Reportes - Ver métricas y reportes"),
            ("7", "🧠  Knowledge Base - Tips y estrategias"),
            ("8", "🐘  Facebook Poster - Publicación automática"),
            ("9", "⚙️   Configuración"),
            ("0", "❌  Salir"),
        ]
        for num, desc in options:
            self._print(f"  {num}  {desc}")

        choice = Prompt.ask("\n👉 ¿Qué deseas hacer?",
                            choices=[str(o[0]) for o in options])

        actions = {
            "1": self._show_strategy_pillars,
            "2": self._manage_campaigns,
            "3": self._manage_groups,
            "4": self._manage_content,
            "5": self._manage_leads,
            "6": self._show_reports,
            "7": self._show_knowledge_base,
            "8": self._manage_facebook_poster,
            "9": self._show_config,
            "0": self._exit,
        }
        action = actions.get(choice)
        if action:
            action()

    # ─── Setup Wizard ────────────────────────────────────────────────────

    def _setup_wizard(self):
        """Initial setup wizard."""
        self._panel("⚙️  CONFIGURACIÓN INICIAL",
                    "Responde las siguientes preguntas para personalizar "
                    "tu agente de afiliados.",
                    "cyan")

        niche = self._input("¿Cuál es tu nicho de mercado? (ej: finanzas, salud, marketing)",
                           default="marketing digital")
        fan_page = self._input("¿Nombre de tu Fan Page de Facebook? (opcional)",
                              default="")
        whatsapp = self._input("¿Tu número de WhatsApp (con código de país)? (opcional)",
                              default="")

        self.strategy.update_config(
            niche=niche,
            fan_page_name=fan_page,
            whatsapp_number=whatsapp
        )

        self._print("\n✅ Configuración guardada exitosamente.", "success")
        self._print(f"\n📌 Nicho: {niche}")
        if fan_page:
            self._print(f"📌 Fan Page: {fan_page}")
        if whatsapp:
            self._print(f"📌 WhatsApp: {whatsapp}")

        # Auto-create first campaign
        camp = self.strategy.create_campaign(
            name=f"Campaña {niche.title()}",
            niche=niche,
            target_sales=10
        )
        self.current_campaign = camp
        self._print(f"\n🎯 Campaña '{camp.name}' creada automáticamente.", "success")

    # ─── Strategy Pillars ────────────────────────────────────────────────

    def _show_strategy_pillars(self):
        """Display the 6 strategic pillars."""
        self._clear()
        self._panel("🎯 ESTRATEGIA DE AFILIADOS - LOS 6 PILARES",
                    "Basado en la metodología: Grupos de Facebook + Hotmart",
                    "cyan")

        for pillar in self.strategy.PILLARS:
            icon = pillar["icon"]
            name = pillar["name"]
            desc = pillar["description"]
            self._print(f"\n{icon}  [bold]{name}[/bold]"
                        if RICH_AVAILABLE else f"\n{icon}  {name}")
            self._print(f"     {desc}")

        self._print("\n" + "-" * 50)
        pillar_id = Prompt.ask(
            "¿Ver detalle de algún pilar? (1-6, o Enter para volver)",
            choices=["1", "2", "3", "4", "5", "6", ""],
            default=""
        )

        if pillar_id:
            guidance = self.strategy.get_pillar_guidance(int(pillar_id))
            if guidance:
                self._panel(
                    f"{guidance['pillar']['icon']} {guidance['pillar']['name']}",
                    "\n".join(
                        f"{i+1}. {step}"
                        for i, step in enumerate(
                            guidance.get("guidance", {}).get("steps", [])
                        )
                    ),
                    "green"
                )
                warning = guidance.get("guidance", {}).get("warning", "")
                if warning:
                    self._print(f"\n⚠️  {warning}", "warning")

            if self._confirm("\n¿Volver al menú principal?"):
                return

    # ─── Campaign Management ─────────────────────────────────────────────

    def _manage_campaigns(self):
        """Campaign management menu."""
        self._clear()
        options = [
            ("1", "📋  Listar campañas"),
            ("2", "➕  Crear nueva campaña"),
            ("3", "📌  Seleccionar campaña activa"),
            ("4", "📝  Editar campaña"),
            ("5", "📊  Avanzar estado de campaña"),
            ("6", "💰  Registrar venta"),
            ("7", "🗑️   Eliminar campaña"),
            ("8", "🔙  Volver"),
        ]

        while True:
            self._panel("📦 GESTIÓN DE CAMPAÑAS",
                        "Administra tus campañas de afiliados",
                        "cyan")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._list_campaigns()
            elif choice == "2":
                self._create_campaign()
            elif choice == "3":
                self._select_campaign()
            elif choice == "4":
                self._edit_campaign()
            elif choice == "5":
                self._advance_campaign()
            elif choice == "6":
                self._record_sale()
            elif choice == "7":
                self._delete_campaign()
            elif choice == "8":
                break

    def _list_campaigns(self):
        """List all campaigns."""
        campaigns = self.strategy.campaigns
        if not campaigns:
            self._print("No hay campañas creadas aún.", "warning")
            return

        rows = []
        for c in campaigns:
            is_active = "◄ ACTIVA" if (self.current_campaign and
                                        c.name == self.current_campaign.name) else ""
            rows.append([
                c.name,
                c.niche or "—",
                c.status,
                f"{c.current_sales}/{c.target_sales}",
                is_active
            ])

        self._table("CAMPAÑAS", ["Nombre", "Nicho", "Estado",
                                 "Ventas", "Activa"], rows)

    def _create_campaign(self):
        """Create a new campaign."""
        self._print("\n=== NUEVA CAMPAÑA ===", "title")
        name = self._input("Nombre de la campaña")
        product = self._input("Nombre del producto a promocionar (opcional)",
                             default="")
        niche = self._input("Nicho (Enter para usar el configurado)",
                           default=self.strategy.config.niche)
        target = int(self._input("Meta de ventas", default="10"))

        camp = self.strategy.create_campaign(
            name=name, product=product, niche=niche,
            target_sales=target
        )

        # Also create in campaign_manager
        self.campaign_manager.create(
            name=name, product=product, niche=niche,
            sales_target=target
        )

        self._print(f"\n✅ Campaña '{name}' creada exitosamente.", "success")
        if self._confirm("¿Establecer como campaña activa?"):
            self.current_campaign = camp

    def _select_campaign(self):
        """Select active campaign."""
        campaigns = self.strategy.campaigns
        if not campaigns:
            self._print("No hay campañas. Crea una primero.", "warning")
            return

        self._list_campaigns()
        name = self._input("Nombre de la campaña a seleccionar")
        camp = self.strategy.get_campaign(name)
        if camp:
            self.current_campaign = camp
            self._print(f"✅ Campaña '{name}' seleccionada.", "success")
        else:
            self._print(f"❌ Campaña '{name}' no encontrada.", "error")

    def _edit_campaign(self):
        """Edit campaign details."""
        if not self.current_campaign:
            self._print("No hay campaña activa. Selecciona una primero.", "warning")
            return

        camp = self.current_campaign
        self._panel(f"EDITANDO: {camp.name}",
                    "Deja vacío para mantener el valor actual")

        product = self._input("Producto", default=camp.product)
        niche = self._input("Nicho", default=camp.niche)
        url = self._input("URL del producto", default=camp.product_url)

        self.strategy.update_config(niche=niche)
        self.current_campaign.product = product
        self.current_campaign.niche = niche
        self.current_campaign.product_url = url
        self.strategy.save_campaigns()

        self._print("✅ Campaña actualizada.", "success")

    def _advance_campaign(self):
        """Advance campaign status."""
        if not self.current_campaign:
            self._print("No hay campaña activa.", "warning")
            return

        statuses = ["draft", "setup", "active", "completed"]
        current = self.current_campaign.status
        try:
            idx = statuses.index(current)
            if idx < len(statuses) - 1:
                next_status = statuses[idx + 1]
                if self._confirm(f"¿Avanzar de '{current}' a '{next_status}'?"):
                    self.current_campaign.status = next_status
                    self.strategy.save_campaigns()
                    self.campaign_manager.advance_status(self.current_campaign.name)
                    self._print(f"✅ Campaña ahora en estado: {next_status}", "success")
            else:
                self._print("La campaña ya está completada.", "info")
        except ValueError:
            self._print(f"Estado desconocido: {current}", "error")

    def _record_sale(self):
        """Record a sale."""
        if not self.current_campaign:
            self._print("No hay campaña activa.", "warning")
            return

        self._print(f"Registrando venta para: {self.current_campaign.name}")
        amount = float(self._input("Monto de la venta ($)", default="0"))
        self.strategy.get_campaign(self.current_campaign.name).current_sales += 1
        self.current_campaign.current_sales += 1
        self.strategy.save_campaigns()
        self.campaign_manager.record_sale(self.current_campaign.name, amount)
        self._print("✅ Venta registrada.", "success")

    def _delete_campaign(self):
        """Delete a campaign."""
        self._list_campaigns()
        name = self._input("Nombre de la campaña a eliminar")
        if self._confirm(f"⚠️  ¿Estás seguro de eliminar '{name}'?"):
            if self.strategy.delete_campaign(name):
                self.campaign_manager.delete(name)
                if self.current_campaign and self.current_campaign.name == name:
                    self.current_campaign = None
                self._print(f"✅ Campaña '{name}' eliminada.", "success")
            else:
                self._print(f"❌ Campaña '{name}' no encontrada.", "error")

    # ─── Group Management ────────────────────────────────────────────────

    def _manage_groups(self):
        """Group management menu."""
        self._clear()
        options = [
            ("1", "🔍  Buscar grupos (palabras clave)"),
            ("2", "➕  Añadir grupo prospecto"),
            ("3", "📋  Listar grupos por estado"),
            ("4", "📊  Ver pipeline de grupos"),
            ("5", "✅  Evaluar grupo (checklist de calidad)"),
            ("6", "📝  Actualizar estado de grupo"),
            ("7", "💡  Sugerencias de acción"),
            ("8", "🔙  Volver"),
        ]

        while True:
            self._panel("🔍 GESTIÓN DE GRUPOS DE FACEBOOK",
                        "Embudo de selección: descubre, prueba y activa grupos",
                        "cyan")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._search_groups_keywords()
            elif choice == "2":
                self._add_group()
            elif choice == "3":
                self._list_groups()
            elif choice == "4":
                self._group_pipeline()
            elif choice == "5":
                self._group_checklist()
            elif choice == "6":
                self._update_group_status()
            elif choice == "7":
                self._group_suggestions()
            elif choice == "8":
                break

    def _search_groups_keywords(self):
        """Show keywords for finding groups."""
        niche = self.strategy.config.niche or self._input(
            "¿Para qué nicho buscar grupos?", default="marketing digital")
        keywords = self.group_finder.get_search_keywords(niche)

        self._panel(f"🔑 PALABRAS CLAVE PARA BUSCAR GRUPOS DE {niche.upper()}",
                    "\n".join(f"  • {kw}" for kw in keywords),
                    "green")
        self._print("\n💡 Busca en Facebook con estas combinaciones.", "info")

    def _add_group(self):
        """Add a new group prospect."""
        name = self._input("Nombre del grupo de Facebook")
        url = self._input("URL del grupo (opcional)", default="")
        niche = self._input("Nicho del grupo", default=self.strategy.config.niche)
        members = int(self._input("Número aproximado de miembros", default="0"))

        self.group_finder.add_prospect(
            name=name, url=url, niche=niche, member_count=members
        )

        if self.current_campaign:
            self.strategy.add_group(
                self.current_campaign.name,
                Group(name=name, niche=niche, member_count=members)
            )

        self._print(f"✅ Grupo '{name}' añadido como prospecto.", "success")

    def _list_groups(self):
        """List groups by status."""
        self._print("\nEstados disponibles:")
        statuses = ["discovered", "pending_test", "testing", "active", "rejected"]
        for i, s in enumerate(statuses, 1):
            groups = self.group_finder.get_groups_by_status(s)
            status_names = {
                "discovered": "Descubiertos",
                "pending_test": "Pendientes de prueba",
                "testing": "En prueba",
                "active": "Activos",
                "rejected": "Rechazados"
            }
            self._print(f"  {i}. {status_names.get(s, s)} ({len(groups)})")

        choice = int(self._input("\nSelecciona un estado (1-5)", default="1"))
        if 1 <= choice <= 5:
            status = statuses[choice - 1]
            groups = self.group_finder.get_groups_by_status(status)
            if groups:
                rows = [[g.name, g.niche, str(g.member_count),
                         str(g.engagement_score) if g.engagement_score else "—"]
                        for g in groups]
                self._table(f"GRUPOS: {status.upper()}",
                           ["Nombre", "Nicho", "Miembros", "Engagement"], rows)
            else:
                self._print(f"No hay grupos en estado '{status}'.", "info")

    def _group_pipeline(self):
        """Show group pipeline summary."""
        summary = self.group_finder.get_pipeline_summary()
        self._panel("📊 PIPELINE DE GRUPOS",
                    f"""
    Total prospectos:     {summary['total_prospects']}
    Descubiertos:         {summary['discovered']}
    Pendientes de prueba: {summary['pending_test']}
    En prueba:            {summary['testing']}
    Activos:              {summary['active']}  ✅
    Rechazados:           {summary['rejected']}
    ─────────────────────────
    Permiten promoción:   {summary['allows_promotion']}
    Alto engagement:      {summary['high_engagement']}
                    """,
                    "green")

    def _group_checklist(self):
        """Show quality checklist."""
        checklist = self.group_finder.get_quality_checklist()
        self._panel("✅ CHECKLIST DE CALIDAD DE GRUPOS",
                    "\n".join(
                        f"  {'☐' if 'Crítica' in c['weight'] or 'Alta' in c['weight'] else '○'} "
                        f"{c['criteria']} ({c['weight']})"
                        for c in checklist
                    ),
                    "yellow")
        self._print("\n💡 Usa esta lista para evaluar cada grupo antes de invertir tiempo.", "info")

    def _update_group_status(self):
        """Update a group's status."""
        name = self._input("Nombre del grupo a actualizar")
        statuses = ["discovered", "pending_test", "testing", "active", "rejected"]
        self._print("Estados: 1=Descubierto, 2=Pendiente prueba, "
                     "3=En prueba, 4=Activo, 5=Rechazado")
        choice = int(self._input("Nuevo estado", default="1"))

        allows = None
        if choice == 4:  # active
            allows = self._confirm("¿Permite publicaciones promocionales?")

        score = None
        if choice in (3, 4):
            score = int(self._input("Puntuación de engagement (0-100)", default="50"))

        if 1 <= choice <= 5:
            self.group_finder.update_status(
                name, statuses[choice - 1],
                allows_promotion=allows, engagement_score=score
            )
            self._print(f"✅ Grupo '{name}' actualizado.", "success")

    def _group_suggestions(self):
        """Show suggested next actions for groups."""
        suggestions = self.group_finder.suggest_next_actions()
        self._panel("💡 SUGERENCIAS DE ACCIÓN",
                    "\n".join(f"  • {s}" for s in suggestions),
                    "cyan")

    # ─── Content Planning ────────────────────────────────────────────────

    def _manage_content(self):
        """Content planning menu."""
        self._clear()
        options = [
            ("1", "🎨  Generar ideas de contenido (80/20)"),
            ("2", "📅  Planificar semana"),
            ("3", "📋  Ver calendario semanal"),
            ("4", "📊  Estadísticas 80/20"),
            ("5", "✅  Marcar contenido como publicado"),
            ("6", "🔙  Volver"),
        ]

        while True:
            self._panel("📊 PLANIFICADOR DE CONTENIDO 80/20",
                        "80% valor • 20% promoción",
                        "cyan")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._generate_content_ideas()
            elif choice == "2":
                self._schedule_week()
            elif choice == "3":
                self._show_calendar()
            elif choice == "4":
                self._content_stats()
            elif choice == "5":
                self._mark_posted()
            elif choice == "6":
                break

    def _generate_content_ideas(self):
        """Generate content ideas."""
        niche = self.strategy.config.niche
        count = int(self._input("¿Cuántas ideas generar?", default="10"))

        ideas = self.content_planner.generate_ideas(niche, count)
        self._print(f"\n✅ {len(ideas)} ideas generadas con ratio 80/20.", "success")

        value = sum(1 for i in ideas if i.content_type == "value")
        promo = sum(1 for i in ideas if i.content_type == "promotion")

        self._panel("IDEAS GENERADAS",
                    f"   🎯 Valor: {value}  |  💰 Promoción: {promo}\n"
                    + "\n".join(
                        f"  {'📚' if i.content_type == 'value' else '🛒'} {i.title}"
                        for i in ideas
                    ),
                    "green")

    def _schedule_week(self):
        """Schedule content for the week."""
        scheduled = self.content_planner.schedule_week()
        if scheduled:
            self._print(f"✅ {len(scheduled)} contenidos programados para la semana.", "success")
            for s in scheduled:
                icon = "📚" if s.content_type == "value" else "🛒"
                self._print(f"  {s.scheduled_date} {icon} {s.title}")
        else:
            self._print("❌ No hay suficientes ideas. Genera más primero.", "warning")

    def _show_calendar(self):
        """Show weekly calendar."""
        calendar = self.content_planner.get_weekly_calendar()
        if not any(calendar.values()):
            self._print("No hay contenido programado aún. Programa una semana primero.", "info")
            return

        for day, ideas in calendar.items():
            if ideas:
                self._print(f"\n[bold]{day}[/bold]" if RICH_AVAILABLE else f"\n{day}")
                for idea in ideas:
                    icon = "📚" if idea.content_type == "value" else "🛒"
                    scheduled = f" [{idea.scheduled_date}]" if idea.scheduled_date else ""
                    status = " ✅" if idea.posted else ""
                    self._print(f"    {icon} {idea.title}{scheduled}{status}")

    def _content_stats(self):
        """Show 80/20 compliance stats."""
        stats = self.content_planner.get_stats()
        compliance = "✅ CUMPLE" if stats["compliant"] else "⚠️  NO CUMPLE"

        self._panel("📊 ESTADÍSTICAS 80/20",
                    f"""
    Total ideas:       {stats['total']}
    Contenido valor:   {stats['value']} ({stats['ratio']*100:.0f}%)
    Contenido promo:   {stats['promotion']} ({(1-stats['ratio'])*100:.0f}%)
    Publicados:        {stats['posted']}
    Programados:       {stats['scheduled']}
    ─────────────────────────
    Ratio actual:      {stats['ratio']*100:.0f}%
    Ratio objetivo:    80%
    {compliance}
                    """,
                    "green" if stats["compliant"] else "yellow")

    def _mark_posted(self):
        """Mark content as posted."""
        title = self._input("Título del contenido publicado")
        engagement = self._input("¿Resultado? (likes, comentarios, etc)", default="")
        if self.content_planner.mark_posted(title, engagement):
            self._print("✅ Marcado como publicado.", "success")
        else:
            self._print("❌ Contenido no encontrado o ya publicado.", "error")

    # ─── Lead Management ─────────────────────────────────────────────────

    def _manage_leads(self):
        """Lead management menu."""
        self._clear()
        options = [
            ("1", "➕  Registrar nuevo lead"),
            ("2", "📋  Ver pipeline de leads"),
            ("3", "🔄  Actualizar estado de lead"),
            ("4", "📞  Leads que requieren seguimiento"),
            ("5", "💬  Ver plantilla de mensaje"),
            ("6", "🔗  Generar enlace wa.link"),
            ("7", "📊  Reporte semanal de leads"),
            ("8", "🔙  Volver"),
        ]

        while True:
            self._panel("💬 GESTIÓN DE LEADS WHATSAPP",
                        "Convierte leads en ventas con seguimiento personalizado",
                        "cyan")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._add_lead()
            elif choice == "2":
                self._lead_pipeline()
            elif choice == "3":
                self._update_lead_status()
            elif choice == "4":
                self._leads_needing_followup()
            elif choice == "5":
                self._message_templates()
            elif choice == "6":
                self._generate_waling()
            elif choice == "7":
                self._lead_weekly_report()
            elif choice == "8":
                break

    def _add_lead(self):
        """Register a new lead."""
        self._print("\n=== NUEVO LEAD ===", "title")
        name = self._input("Nombre del lead")
        phone = self._input("WhatsApp (con código de país, ej: +584141234567)")

        source = ""
        if self.current_campaign:
            source = self._input("¿De qué grupo llegó?", default="")

        lead = self.lead_tracker.add_lead(
            name=name, phone=phone, source_group=source
        )

        if self.current_campaign:
            self.strategy.add_lead(
                self.current_campaign.name,
                Lead(name=name, phone=phone, source_group=source)
            )

        self._print(f"✅ Lead '{name}' registrado.", "success")
        self._print(f"\n💡 Mensaje inicial sugerido:")
        msg = self.lead_tracker.get_message_template("new", {
            "nombre": name, "producto": self.current_campaign.product
            if self.current_campaign else "[Producto]"
        })
        self._print(msg, "info")

    def _lead_pipeline(self):
        """Show lead pipeline."""
        summary = self.lead_tracker.get_pipeline_summary()
        self._panel("📊 PIPELINE DE LEADS",
                    f"""
    Total leads:        {summary['total']}
    🆕 Nuevos:          {summary['new']}
    📞 Contactados:     {summary['contacted']}
    📅 Reunión:         {summary['meeting_set']}
    🔥 Interesados:     {summary['interested']}
    🤝 Negociación:     {summary['negotiation']}
    ✅ Cerrados:        {summary['closed']}
    ❌ Perdidos:        {summary['lost']}
    ─────────────────────────
    Tasa de conversión: {summary['conversion_rate']}%
    Seguimientos hoy:   {summary['follow_ups_today']}
                    """,
                    "green")

    def _update_lead_status(self):
        """Update a lead's status."""
        phone = self._input("WhatsApp del lead (para identificar)")
        statuses = {
            "1": "new", "2": "contacted", "3": "meeting_set",
            "4": "interested", "5": "negotiation", "6": "closed", "7": "lost"
        }
        self._print("Estados:")
        for k, v in statuses.items():
            self._print(f"  {k}. {v}")
        choice = self._input("Nuevo estado", default="1")
        notes = self._input("Notas (opcional)", default="")

        status = statuses.get(choice)
        if status:
            self.lead_tracker.update_status(phone, status, notes)
            if self.current_campaign:
                self.strategy.update_lead_status(
                    self.current_campaign.name, phone, status
                )
            self._print(f"✅ Lead actualizado a: {status}", "success")

    def _leads_needing_followup(self):
        """Show leads needing follow-up."""
        needing = self.lead_tracker.get_leads_needing_followup()
        if not needing:
            self._print("No hay leads que requieran seguimiento hoy.", "info")
            return

        self._panel("📞 LEADS QUE REQUIEREN SEGUIMIENTO",
                    "\n".join(
                        f"  • {lead.name} ({lead.phone}) - {step['type']}"
                        for lead, step in needing
                    ),
                    "yellow")
        self._print("\n💡 Revisa la sección de plantillas para mensajes sugeridos.", "info")

    def _message_templates(self):
        """Show message templates."""
        template_keys = list(self.lead_tracker.MESSAGE_TEMPLATES.keys())
        self._print("Plantillas disponibles:")
        for i, key in enumerate(template_keys, 1):
            self._print(f"  {i}. {key}")

        choice = int(self._input("\nSelecciona una plantilla (1-6)", default="1"))
        if 1 <= choice <= len(template_keys):
            key = template_keys[choice - 1]
            msg = self.lead_tracker.get_message_template(key)
            self._panel(f"💬 PLANTILLA: {key}",
                        msg,
                        "cyan")

    def _generate_waling(self):
        """Generate a wa.link URL."""
        phone = self._input("Tu número de WhatsApp (con código de país)",
                           default=self.strategy.config.whatsapp_number)
        link = self.lead_tracker.generate_waling_link(phone)
        self._panel("🔗 TU ENLACE WHATSAPP",
                    f"{link}\n\n💡 Pon este enlace en tu biografía de Facebook "
                    "y en tus publicaciones promocionales.",
                    "green")

    def _lead_weekly_report(self):
        """Show weekly lead report."""
        report = self.lead_tracker.get_weekly_report()
        self._panel("📊 REPORTE SEMANAL DE LEADS",
                    f"""
    Nuevos esta semana:    {report['new_this_week']}
    Cerrados esta semana:  {report['closed_this_week']}
    Seguimientos pendientes: {report['pending_followups']}
    ─────────────────────────
    Pipeline completo:
    • Nuevos:      {report['pipeline']['new']}
    • Contactados: {report['pipeline']['contacted']}
    • Interesados: {report['pipeline']['interested']}
    • Cerrados:    {report['pipeline']['closed']}
    • Tasa conv:   {report['pipeline']['conversion_rate']}%
                    """,
                    "green")

    # ─── Reports ─────────────────────────────────────────────────────────

    def _show_reports(self):
        """Show reports and metrics."""
        self._clear()
        options = [
            ("1", "📊  Reporte completo de campaña"),
            ("2", "📈  Métricas clave"),
            ("3", "🗓️   Horario semanal recomendado"),
            ("4", "🏆  Nichos rentables"),
            ("5", "📤  Exportar reporte"),
            ("6", "🔙  Volver"),
        ]

        while True:
            self._panel("📈 REPORTES Y MÉTRICAS",
                        "Monitorea tu progreso y resultados",
                        "cyan")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._campaign_report()
            elif choice == "2":
                self._key_metrics()
            elif choice == "3":
                self._weekly_schedule()
            elif choice == "4":
                self._profitable_niches()
            elif choice == "5":
                self._export_report()
            elif choice == "6":
                break

    def _campaign_report(self):
        """Show full campaign report."""
        if not self.current_campaign:
            self._print("No hay campaña activa.", "warning")
            return

        report = self.strategy.export_campaign_report(
            self.current_campaign.name
        )
        if "error" in report:
            self._print(report["error"], "error")
            return

        stats = report.get("content", {})
        compliance = "✅" if stats.get("compliant") else "⚠️"

        self._panel(f"📊 REPORTE: {report['campaign']}",
                    f"""
    Producto: {report['product']}
    Nicho: {report['niche']}
    Estado: {report['status']}
    Ventas: {report['current_sales']}/{report['target_sales']}
    ─────────────────────────
    GRUPOS:
    • Activos: {report['groups']['allowed']}
    • Probados: {report['groups']['allowed'] + report['groups']['blocked']}
    • Pendientes: {report['groups']['untested']}
    ─────────────────────────
    CONTENIDO 80/20 {compliance}:
    • Valor: {stats['value']}  |  Promo: {stats['promotion']}
    • Ratio: {stats['ratio']*100:.0f}%
    • Publicados: {stats.get('posted', 'N/A')}
    ─────────────────────────
    LEADS:
    • Totales: {report['leads']['total']}
    • Cerrados: {report['leads']['closed']}
    • Tasa: {report['leads']['total'] and round(report['leads']['closed']/report['leads']['total']*100, 1) or 0}%
                    """,
                    "green")

    def _key_metrics(self):
        """Show key metrics to track."""
        self._panel("📈 MÉTRICAS CLAVE A SEGUIR",
                    "\n".join(
                        f"  • {m['metrica']}: {m['porque']}"
                        for m in KnowledgeBase.KEY_METRICS
                    ),
                    "cyan")

    def _weekly_schedule(self):
        """Show recommended weekly schedule."""
        schedule = self.strategy.get_weekly_schedule()
        self._panel("🗓️  HORARIO SEMANAL RECOMENDADO",
                    "\n\n".join(
                        f"[bold]{day['day']}[/bold]\n"
                        f"  🌅 Mañana: {day['morning']}\n"
                        f"  ☀️  Tarde: {day['afternoon']}\n"
                        f"  🌙 Noche: {day['night']}"
                        for day in schedule
                    ) if RICH_AVAILABLE else "\n\n".join(
                        f"{day['day']}\n"
                        f"  Mañana: {day['morning']}\n"
                        f"  Tarde: {day['afternoon']}\n"
                        f"  Noche: {day['night']}"
                        for day in schedule
                    ),
                    "green")

    def _profitable_niches(self):
        """Show profitable niches."""
        self._panel("🏆 NICHOS RENTABLES PARA AFILIADOS",
                    "\n".join(
                        f"{n['nivel']} {n['nombre']}: {n['descripcion']}"
                        for n in KnowledgeBase.PROFITABLE_NICHES
                    ),
                    "green")

    def _export_report(self):
        """Export campaign report."""
        if not self.current_campaign:
            self._print("No hay campaña activa.", "warning")
            return

        report = self.strategy.export_campaign_report(
            self.current_campaign.name
        )
        if "error" in report:
            self._print(report["error"], "error")
            return

        import json
        export_path = os.path.join(self.data_dir,
                                   f"report_{self.current_campaign.name}_{datetime.now().strftime('%Y%m%d')}.json")
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self._print(f"✅ Reporte exportado a: {export_path}", "success")

    # ─── Knowledge Base ──────────────────────────────────────────────────

    def _show_knowledge_base(self):
        """Show knowledge base."""
        self._clear()
        options = [
            ("1", "🧠  Psicología de venta"),
            ("2", "💬  Frases de engagement"),
            ("3", "📚  Tipos de contenido de valor"),
            ("4", "🌡️   Warm up para grupos"),
            ("5", "📖  Guión de WhatsApp"),
            ("6", "🔙  Volver"),
        ]

        while True:
            self._panel("🧠 KNOWLEDGE BASE",
                        "Estrategias, frases y técnicas probadas",
                        "cyan")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._show_sales_psychology()
            elif choice == "2":
                self._show_engagement_phrases()
            elif choice == "3":
                self._show_value_content()
            elif choice == "4":
                self._show_warmup()
            elif choice == "5":
                self._show_whatsapp_script()
            elif choice == "6":
                break

    def _show_sales_psychology(self):
        """Show sales psychology tips."""
        self._panel("🧠 PSICOLOGÍA DE VENTA",
                    "\n".join(f"  • {tip}" for tip in KnowledgeBase.SALES_PSYCHOLOGY_TIPS),
                    "magenta")

    def _show_engagement_phrases(self):
        """Show engagement phrases."""
        for category, phrases in KnowledgeBase.ENGAGEMENT_PHRASES.items():
            self._panel(f"💬 FRASES DE {category.upper()}",
                        "\n".join(f"  • {p}" for p in phrases),
                        "cyan")

    def _show_value_content(self):
        """Show value content types."""
        rows = [[c["tipo"], c["ejemplo"], c["formato"]]
                for c in KnowledgeBase.VALUE_CONTENT_TYPES]
        self._table("TIPOS DE CONTENIDO DE VALOR",
                   ["Tipo", "Ejemplo", "Formato"], rows)

    def _show_warmup(self):
        """Show group warmup tips."""
        self._panel("🌡️  WARM UP PARA GRUPOS",
                    "\n".join(
                        f"  • {tip}" for tip in KnowledgeBase.GROUP_WARMUP_TIPS
                    ),
                    "yellow")

    def _show_whatsapp_script(self):
        """Show WhatsApp script."""
        script = KnowledgeBase.WHATSAPP_SCRIPT
        self._panel("📖 GUIÓN DE WHATSAPP",
                    f"""
    💬 SALUDO INICIAL:
    {script['saludo_inicial']}

    🔍 DESCUBRIMIENTO:
    {script['descubrimiento']}

    🎯 PRESENTACIÓN DE VALOR:
    {script['presentacion_valor']}

    ❓ OBJECIONES COMUNES:
    {chr(10).join(f'  • {k}: {v}' for k, v in script['manejo_objecciones'].items())}

    🏁 CIERRE:
    {script['cierre']}
                    """,
                    "cyan")

    # ─── Facebook Poster ─────────────────────────────────────────────────

    def _manage_facebook_poster(self):
        """Facebook Poster management menu."""
        self._clear()
        options = [
            ("1", "🐘  Ver estado del Facebook Poster"),
            ("2", "🔧  Configurar perfil de Chrome (iniciar sesión en FB)"),
            ("3", "🚀  Publicar en grupos activos ahora"),
            ("4", "✅  Habilitar/Deshabilitar publicación automática"),
            ("5", "📊  Ver estadísticas"),
            ("6", "🔙  Volver"),
        ]

        while True:
            self._panel("🐘 FACEBOOK POSTER — Publicación Automática",
                        "Automatiza tus publicaciones en grupos de Facebook "
                        "usando SeleniumBase",
                        "magenta")
            choice = self._menu("Opciones:", options)
            if choice == "1":
                self._fb_status()
            elif choice == "2":
                self._fb_setup_profile()
            elif choice == "3":
                self._fb_post_now()
            elif choice == "4":
                self._fb_toggle()
            elif choice == "5":
                self._fb_stats()
            elif choice == "6":
                break

    def _fb_status(self):
        """Show Facebook Poster status."""
        try:
            status = self.facebook_poster.get_session_status()
            self._panel("🐘 ESTADO DEL FACEBOOK POSTER",
                        f"""
    Habilitado:        {'✅ Sí' if self.facebook_poster.config.enabled else '❌ No'}
    Perfil Chrome:     {'✅ Existe' if status['profile_exists'] else '❌ Pendiente'}
    Cookies guardadas: {'✅ Sí' if status['cookies_exist'] else '❌ No'}
    Límite diario:     {status['max_posts_per_day']}
    Posts hoy:         {status['posts_today']}
    Restantes hoy:     {status['remaining_today']}
    Total posteos:     {status['total_posts_logged']}
    Últimas 24h:       {status['last_24h_posts']}
                        """,
                        "cyan")
            if not status['profile_exists']:
                self._print("\n💡 Configura tu perfil primero: Opción 2", "info")
        except Exception as e:
            self._print(f"❌ Error: {e}", "error")

    def _fb_setup_profile(self):
        """Setup Chrome profile for Facebook."""
        self._print("\n🔧 Abriendo Chrome para configurar perfil...", "info")
        self._print("   Sigue las instrucciones en la ventana de Chrome.", "info")
        try:
            self.facebook_poster.setup_profile()
        except Exception as e:
            self._print(f"❌ Error: {e}", "error")

    def _fb_post_now(self):
        """Execute automatic posting."""
        if not self.facebook_poster.config.enabled:
            if self._confirm("⚠️ Facebook Poster no está habilitado. ¿Habilitarlo?"):
                self.facebook_poster.update_config(enabled=True)
            else:
                return

        status = self.facebook_poster.get_session_status()
        if not status["profile_exists"]:
            self._print("❌ Perfil de Chrome no configurado.", "error")
            self._print("   Ve a Opción 2 para configurarlo.", "info")
            return

        max_posts = int(self._input("¿Cuántos posts publicar?", default="3"))
        self._print(f"\n🚀 Publicando en {max_posts} grupos...", "title")
        self._print("   ⏳ Esto puede tomar varios minutos...\n", "info")

        try:
            results = self.facebook_poster.post_to_active_groups(max_posts=max_posts)
            success = sum(1 for r in results if r.success)
            self._print(f"\n📊 Resultados: {success}/{len(results)} exitosos", "success" if success > 0 else "warning")
            for r in results:
                icon = "✅" if r.success else "❌"
                self._print(f"  {icon} {r.group_name}")
                if r.error:
                    self._print(f"     Error: {r.error}", "error")
        except Exception as e:
            self._print(f"❌ Error general: {e}", "error")

    def _fb_toggle(self):
        """Toggle Facebook Poster enabled/disabled."""
        current = self.facebook_poster.config.enabled
        new_state = not current
        self.facebook_poster.update_config(enabled=new_state)
        status = "✅ Habilitado" if new_state else "❌ Deshabilitado"
        self._print(f"\n🐘 Facebook Poster: {status}", "success" if new_state else "warning")

    def _fb_stats(self):
        """Show Facebook Poster statistics."""
        try:
            stats = self.facebook_poster.get_stats()
            self._panel("📊 ESTADÍSTICAS DEL FACEBOOK POSTER",
                        f"""
    Total publicaciones:   {stats['total_posts']}
    ✅ Exitosas:           {stats['total_success']}
    ❌ Fallidas:           {stats['total_failures']}
    📈 Tasa de éxito:      {stats['success_rate']}%
    📅 Posts hoy:          {stats['posts_today']}
    ⏳ Restantes hoy:      {stats['remaining_today']}
                        """,
                        "green")
        except Exception as e:
            self._print(f"❌ Error: {e}", "error")

    # ─── Configuration ───────────────────────────────────────────────────

    def _show_config(self):
        """Show configuration menu."""
        self._clear()
        config = self.strategy.config

        self._panel("⚙️  CONFIGURACIÓN ACTUAL",
                    f"""
    Nicho:              {config.niche or '❌ No configurado'}
    Fan Page:           {config.fan_page_name or '❌ No configurada'}
    WhatsApp:           {config.whatsapp_number or '❌ No configurado'}
    Publicaciones/día:  {config.daily_posts}
    Ratio 80/20:        {int(config.value_ratio * 100)}% valor
                    """,
                    "cyan")

        if self._confirm("¿Deseas editar la configuración?"):
            niche = self._input("Nicho", default=config.niche)
            fan_page = self._input("Fan Page", default=config.fan_page_name)
            whatsapp = self._input("WhatsApp", default=config.whatsapp_number)

            self.strategy.update_config(
                niche=niche,
                fan_page_name=fan_page,
                whatsapp_number=whatsapp
            )
            self._print("✅ Configuración actualizada.", "success")

    def _exit(self):
        """Exit the application."""
        # Cleanup database connections
        try:
            self.group_finder.db.close()
            self.content_planner.db.close()
            self.lead_tracker.db.close()
        except Exception:
            pass
        self._print("\n¡Gracias por usar Afiliados AI Agent!", "success")
        if self._confirm("¿Estás seguro de que deseas salir?"):
            self._print("\n¡Gracias por usar Afiliados AI Agent!", "success")
            self._print("Recuerda: la constancia es la clave del éxito. 🚀", "info")
            self.running = False


def main():
    """Main entry point."""
    cli = AffiliateCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        cli._print("\n\n👋 ¡Hasta luego!", "info")
        sys.exit(0)


if __name__ == "__main__":
    main()
