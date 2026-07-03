#!/usr/bin/env python3
"""
Afiliados AI Agent - Punto de entrada principal.

Uso:
    python run.py                    # Inicia la CLI interactiva
    python run.py --dashboard        # Inicia el dashboard web
    python run.py --fb-post          # Publica automáticamente en grupos
    python run.py --fb-setup         # Configura perfil de Chrome para FB
    python run.py --help             # Muestra ayuda
"""

import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Afiliados AI Agent - Estrategia de marketing de afiliados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run.py                    # Iniciar CLI interactiva
  python run.py --dashboard        # Iniciar dashboard web
  python run.py --fb-post          # Publicar automáticamente en grupos
  python run.py --fb-setup         # Configurar perfil de Chrome
  python run.py --fb-status        # Ver estado del Facebook Poster
  python run.py --version          # Mostrar versión
        """
    )
    parser.add_argument("--dashboard", action="store_true",
                       help="Iniciar el dashboard web")
    parser.add_argument("--port", type=int, default=5000,
                       help="Puerto para el dashboard web (default: 5000)")
    parser.add_argument("--version", action="store_true",
                       help="Mostrar versión")
    parser.add_argument("--export", type=str, metavar="CAMPAÑA",
                       help="Exportar reporte de una campaña")
    parser.add_argument("--generate-ideas", type=int, metavar="N",
                       help="Generar N ideas de contenido y salir")
    # Facebook Poster arguments
    parser.add_argument("--fb-post", action="store_true",
                       help="Publicar automáticamente en grupos de Facebook")
    parser.add_argument("--fb-setup", action="store_true",
                       help="Configurar perfil de Chrome para Facebook")
    parser.add_argument("--fb-status", action="store_true",
                       help="Ver estado del Facebook Poster")
    parser.add_argument("--fb-max", type=int, default=5,
                       help="Máximo de posts automáticos (default: 5)")

    args = parser.parse_args()

    if args.version:
        print("Afiliados AI Agent v1.1.0")
        print("Estrategia: Grupos de Facebook + Hotmart")
        print("🐘 Con Facebook Poster (SeleniumBase)")
        return

    if args.dashboard:
        print("🚀 Iniciando dashboard web...")
        from dashboard.api import start_dashboard
        start_dashboard(port=args.port)
        return

    if args.export:
        print(f"📤 Exportando reporte de campaña: {args.export}")
        from agent.strategy import StrategyEngine
        engine = StrategyEngine()
        report = engine.export_campaign_report(args.export)
        if "error" in report:
            print(f"❌ {report['error']}")
            sys.exit(1)
        import json
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.generate_ideas:
        from agent.content_planner import ContentPlanner
        from agent.strategy import StrategyEngine

        engine = StrategyEngine()
        planner = ContentPlanner(
            os.path.join(os.path.expanduser("~"), ".affiliate_agent")
        )
        niche = engine.config.niche or "marketing digital"
        ideas = planner.generate_ideas(niche, args.generate_ideas)
        print(f"\n✅ {len(ideas)} ideas generadas para nicho: {niche}")
        for i, idea in enumerate(ideas, 1):
            icon = "📚" if idea.content_type == "value" else "🛒"
            print(f"{i:2d}. {icon} [{idea.content_type}] {idea.title}")
        return

    # ─── Facebook Poster ────────────────────────────────────────────────
    if args.fb_setup:
        print("🐘 Configurando perfil de Chrome para Facebook...")
        from automation.facebook_poster import FacebookPoster
        poster = FacebookPoster()
        poster.setup_profile()
        return

    if args.fb_status:
        print("🐘 Estado del Facebook Poster:")
        from automation.facebook_poster import FacebookPoster
        poster = FacebookPoster()
        status = poster.get_session_status()
        print(f"  Habilitado:        {'✅ Sí' if poster.config.enabled else '❌ No'}")
        print(f"  Perfil Chrome:     {'✅ Existe' if status['profile_exists'] else '❌ No configurado'}")
        print(f"  Cookies:           {'✅ Guardadas' if status['cookies_exist'] else '❌ Sin cookies'}")
        print(f"  Límite diario:     {status['max_posts_per_day']}")
        print(f"  Posts hoy:         {status['posts_today']}")
        print(f"  Restantes hoy:     {status['remaining_today']}")
        if not status['profile_exists']:
            print(f"\n💡 Ejecuta: python run.py --fb-setup")
        return

    if args.fb_post:
        print("🐘 Iniciando publicación automática en Facebook...")
        from automation.facebook_poster import FacebookPoster
        poster = FacebookPoster()

        if not poster.config.enabled:
            poster.update_config(enabled=True)
            print("✅ Facebook Poster habilitado")

        status = poster.get_session_status()
        if not status["profile_exists"]:
            print("❌ Perfil de Chrome no configurado.")
            print("   Ejecuta: python run.py --fb-setup")
            return

        results = poster.post_to_active_groups(max_posts=args.fb_max)
        print(f"\n📊 Resultados: {sum(1 for r in results if r.success)}/{len(results)} exitosos")
        for r in results:
            icon = "✅" if r.success else "❌"
            print(f"  {icon} {r.group_name}")
        return

    # Default: start CLI
    print("🤖 Iniciando Afiliados AI Agent...")
    from agent.cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
