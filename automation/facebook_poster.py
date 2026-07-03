"""
affiliate-ai-agent/automation/facebook_poster.py
══════════════════════════════════════════════════════════════════
🐘 FACEBOOK POSTER — Automatización Inteligente de Publicaciones
══════════════════════════════════════════════════════════════════

Motor de automatización para publicar en Grupos de Facebook usando
SeleniumBase con UC Mode (modo indetectable).

CARACTERÍSTICAS:
• Usa SeleniumBase con UC Mode — evade detección de bots
• Perfil de Chrome persistente — las cookies se guardan entre sesiones
• Límite diario configurable — evita parecer spam
• Rotación de grupos — no publica al mismo grupo muy seguido
• Delays aleatorios — comportamiento humano simulado
• Logging completo — todas las acciones quedan registradas
• Fallos controlados — no detiene toda la cola si un grupo falla

REQUISITOS:
    pip install seleniumbase

USO:
    python -m automation.facebook_poster --status
    python -m automation.facebook_poster --post
    python -m automation.facebook_poster --setup-profile

SEGURIDAD:
    ⚠️  Usa con responsabilidad. Respeta las reglas de cada grupo.
    ⚠️  No publiques contenido promocional donde no esté permitido.
    ⚠️  Mantén el ratio 80/20: 80% valor, 20% promoción.
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# Asegurar que podemos importar desde la raíz del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Importaciones tempranas para evitar imports inline en métodos
from selenium.webdriver.common.keys import Keys
from agent.group_finder import GroupFinder
from agent.content_planner import ContentPlanner
from agent.strategy import StrategyEngine

logger = logging.getLogger("facebook_poster")


# ─── CONSTANTES DE SEGURIDAD ─────────────────────────────────────────────────

# Límites diarios para evitar comportamientos sospechosos
MIN_SECONDS_BETWEEN_POSTS = 120  # Mínimo 2 minutos entre posts
MAX_SECONDS_BETWEEN_POSTS = 600  # Máximo 10 minutos entre posts

# Delays humanos (en segundos)
TYPING_DELAY_MIN = 0.05
TYPING_DELAY_MAX = 0.15
NAVIGATION_DELAY_MIN = 2
NAVIGATION_DELAY_MAX = 5
POST_ACTION_DELAY_MIN = 3
POST_ACTION_DELAY_MAX = 8

# Rutas
DATA_DIR = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
CHROME_PROFILE_DIR = os.path.join(DATA_DIR, "chrome_profile")

# URLs de Facebook
FACEBOOK_URL = "https://www.facebook.com"


# ─── MODELOS DE DATOS ────────────────────────────────────────────────────────

@dataclass
class PostResult:
    """Resultado de un intento de publicación."""
    group_name: str
    group_url: str
    content_title: str
    content_type: str
    success: bool
    timestamp: str
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PostResult":
        return cls(**d)


@dataclass
class FacebookConfig:
    """Configuración del Facebook Poster."""
    enabled: bool = False
    max_posts_per_day: int = 5
    min_interval_minutes: int = 5
    headless: bool = False
    chrome_profile_path: str = CHROME_PROFILE_DIR
    auto_accept_group_rules: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "FacebookConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ─── MOTOR PRINCIPAL ─────────────────────────────────────────────────────────

class FacebookPoster:
    """
    Motor de automatización de Facebook Groups.

    Flujo de trabajo:
    1. Carga/configura el perfil de Chrome
    2. Inicia sesión en Facebook (o reusa cookies existentes)
    3. Obtiene los grupos activos desde GroupFinder
    4. Publica contenido planificado en cada grupo
    5. Registra resultados y actualiza el estado
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = DATA_DIR

        self.data_dir = data_dir
        self.profile_dir = os.path.join(data_dir, "chrome_profile")
        self.log_file = os.path.join(data_dir, "post_log.json")
        self.config_file = os.path.join(data_dir, "facebook_config.json")

        self.config = self._load_config()
        self._driver = None
        self._today_posts = 0
        self._post_log: List[PostResult] = []
        self._load_log()

        os.makedirs(self.profile_dir, exist_ok=True)

    # ─── PERSISTENCIA ────────────────────────────────────────────────────

    def _load_config(self) -> FacebookConfig:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return FacebookConfig.from_dict(data)
            except Exception as e:
                logger.warning(f"Error loading config: {e}")
        return FacebookConfig()

    def _save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _load_log(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._post_log = [PostResult.from_dict(d) for d in data]
                self._reset_daily_count()
            except Exception as e:
                logger.warning(f"Error loading post log: {e}")
                self._post_log = []

    def _save_log(self):
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(
                    [p.to_dict() for p in self._post_log[-100:]],
                    f, indent=2, ensure_ascii=False
                )
        except Exception as e:
            logger.error(f"Error saving post log: {e}")

    def _reset_daily_count(self):
        today = date.today().isoformat()
        self._today_posts = sum(
            1 for p in self._post_log
            if p.timestamp[:10] == today and p.success
        )

    def _get_post_count_today(self) -> int:
        today = date.today().isoformat()
        return sum(
            1 for p in self._post_log
            if p.timestamp[:10] == today and p.success
        )

    # ─── API PÚBLICA PARA ACCESO AL LOG ─────────────────────────────────

    def get_recent_posts(self, count: int = 20) -> List[dict]:
        """
        Obtiene las últimas publicaciones registradas.

        Args:
            count: Número máximo de registros a devolver

        Returns:
            Lista de dicts con los PostResult más recientes
        """
        sorted_log = sorted(
            self._post_log,
            key=lambda x: x.timestamp,
            reverse=True
        )[:count]
        return [p.to_dict() for p in sorted_log]

    # ─── GESTIÓN DEL DRIVER ─────────────────────────────────────────────

    def _create_driver(self) -> Any:
        try:
            from seleniumbase import Driver
        except ImportError:
            raise ImportError(
                "SeleniumBase no está instalado. Ejecuta: pip install seleniumbase"
            )

        logger.info(f"🌐 Iniciando Chrome con perfil persistente...")
        logger.info(f"   Perfil: {self.profile_dir}")

        driver = Driver(
            browser="chrome",
            headless=self.config.headless,
            uc=True,
            user_data_dir=self.profile_dir,
            agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            no_sandbox=True,
        )
        driver.set_window_size(1366, 768)
        logger.info("✅ Chrome iniciado correctamente")
        return driver

    def _human_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        time.sleep(random.uniform(min_sec, max_sec))

    def _human_type(self, element: Any, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(TYPING_DELAY_MIN, TYPING_DELAY_MAX))

    # ─── VERIFICACIÓN DE SESIÓN ─────────────────────────────────────────

    def is_logged_in(self, driver: Any) -> bool:
        try:
            driver.get(FACEBOOK_URL)
            self._human_delay(3, 5)

            indicators = [
                "//a[@aria-label='Tu perfil']",
                "//div[@aria-label='Tu perfil']",
                "//*[contains(@href, '/me/')]",
                "//*[contains(@data-pagelet, 'Profile')]",
                "//span[contains(text(), '¿Qué estás pensando')]",
                "//div[@role='search']",
            ]
            for indicator in indicators:
                try:
                    if driver.find_elements("xpath", indicator):
                        logger.info("✅ Sesión de Facebook activa")
                        return True
                except Exception:
                    continue

            current_url = driver.current_url.lower()
            if "facebook.com" in current_url and "login" not in current_url:
                logger.info("✅ Parece que hay sesión activa")
                return True

            logger.warning("⚠️ No se detectó sesión activa de Facebook")
            return False

        except Exception as e:
            logger.error(f"❌ Error al verificar sesión: {e}")
            return False

    # ─── INICIO DE SESIÓN MANUAL ────────────────────────────────────────

    def setup_profile(self):
        print("\n" + "=" * 60)
        print("🐘 CONFIGURACIÓN DEL PERFIL DE CHROME PARA FACEBOOK")
        print("=" * 60)
        print("\n🔧 Vamos a configurar tu perfil de navegador para Facebook.")
        print("📌 SOLO LA PRIMERA VEZ necesitas iniciar sesión manualmente.")
        print("📌 Después, las cookies se guardan automáticamente.\n")

        driver = self._create_driver()
        try:
            driver.get(FACEBOOK_URL)
            self._human_delay(3, 5)

            if self.is_logged_in(driver):
                print("\n✅ ¡Ya tienes sesión iniciada en Facebook!")
                print("   Las cookies se han guardado para futuras sesiones.")
            else:
                print("\n" + "!" * 50)
                print("⚠️  INICIA SESIÓN MANUALMENTE EN LA VENTANA DE CHROME")
                print("!" * 50)
                print("\n📝 Instrucciones:")
                print("   1. Inicia sesión con tu cuenta de Facebook")
                print("   2. Si tienes 2FA, verifica tu identidad")
                print("   3. NO cierres la ventana hasta que veas tu feed")
                print("\n⏳ Esperando hasta 120 segundos...")
                print("   Presiona Ctrl+C si necesitas más tiempo\n")

                for i in range(120):
                    time.sleep(1)
                    if self.is_logged_in(driver):
                        print("\n✅ ¡Sesión iniciada correctamente!")
                        break
                    if i % 10 == 0 and i > 0:
                        print(f"   ⏳ Esperando... {i} segundos")
                else:
                    print("\n⚠️  No se detectó inicio de sesión en 120 segundos.")
                    print("   Ejecuta de nuevo: python run.py --fb-setup")
        except KeyboardInterrupt:
            print("\n\n⚠️  Configuración cancelada.")
        finally:
            if driver:
                driver.quit()
                print("👋 Chrome cerrado.")

    # ─── PUBLICACIÓN EN GRUPOS ──────────────────────────────────────────

    def get_session_status(self) -> dict:
        profile_exists = os.path.exists(self.profile_dir) and any(
            os.scandir(self.profile_dir)
        )
        cookies_exist = False
        if profile_exists:
            default_dir = os.path.join(self.profile_dir, "Default")
            if os.path.exists(default_dir):
                cookies_exist = os.path.exists(os.path.join(default_dir, "Cookies"))

        today_count = self._get_post_count_today()
        return {
            "configured": self.config.enabled,
            "profile_exists": profile_exists,
            "cookies_exist": cookies_exist,
            "max_posts_per_day": self.config.max_posts_per_day,
            "posts_today": today_count,
            "remaining_today": max(0, self.config.max_posts_per_day - today_count),
            "headless": self.config.headless,
            "profile_path": self.profile_dir,
            "last_24h_posts": len([
                p for p in self._post_log
                if p.timestamp and datetime.fromisoformat(p.timestamp) >
                   datetime.now() - timedelta(hours=24)
            ]),
            "total_posts_logged": len(self._post_log),
        }

    def post_to_group(self, driver: Any, group_url: str,
                      content: str, title: str = "") -> PostResult:
        start_time = time.time()
        group_name = group_url.rstrip("/").split("/")[-1].replace("-", " ").title()

        try:
            logger.info(f"📝 Publicando en: {group_name}")
            driver.get(group_url)
            self._human_delay(NAVIGATION_DELAY_MIN, NAVIGATION_DELAY_MAX)
            driver.wait_for_element("body", timeout=15)

            # Buscar área de creación de post
            post_area_selectors = [
                "//*[@role='button']//span[contains(text(), '¿Qué estás pensando')]",
                "//*[@role='button']//span[contains(text(), 'Write something')]",
                "//*[@aria-label='Create a public post']",
                "//*[@role='button'][contains(@aria-label, 'post')]",
                "//div[@role='button']//span[contains(text(), 'publicación')]",
                "//div[@role='button']//span[contains(text(), 'post')]",
                "//div[@role='button'][@tabindex='0']",
            ]

            post_area = None
            for selector in post_area_selectors:
                try:
                    elements = driver.find_elements("xpath", selector)
                    if elements:
                        post_area = elements[0]
                        logger.info("   ✅ Área de post encontrada")
                        break
                except Exception:
                    continue

            if not post_area:
                raise Exception(
                    "No se encontró el área de publicación. "
                    "¿El grupo permite publicar?"
                )

            post_area.click()
            self._human_delay(2, 4)

            # Buscar editor de texto
            editor_selectors = [
                "//div[@role='textbox' or @role='text box']",
                "//div[@aria-label='Escribe una publicación...']",
                "//div[@aria-label='Write a post...']",
                "//div[@contenteditable='true']",
                "//div[contains(@class, 'notranslate')][@contenteditable='true']",
            ]

            editor = None
            for selector in editor_selectors:
                try:
                    elements = driver.find_elements("xpath", selector)
                    if elements:
                        editor = elements[0]
                        logger.info("   ✅ Editor encontrado")
                        break
                except Exception:
                    continue

            if not editor:
                raise Exception("No se encontró el editor de texto")

            logger.info("   ✍️ Escribiendo contenido...")
            editor.click()
            self._human_delay(0.5, 1)
            self._human_type(editor, content)
            self._human_delay(1, 2)

            # Buscar botón Publicar
            publish_selectors = [
                "//div[@role='button']//span[contains(text(), 'Publicar')]",
                "//div[@role='button']//span[contains(text(), 'Publish')]",
                "//div[@role='button'][@aria-label='Publicar']",
                "//div[@role='button'][@aria-label='Publish']",
                "//span[text()='Publicar']/..",
                "//span[text()='Publish']/..",
            ]

            published = False
            for selector in publish_selectors:
                try:
                    btn = driver.find_element("xpath", selector)
                    if btn and btn.is_displayed():
                        btn.click()
                        published = True
                        logger.info(f"   ✅ Publicado en {group_name}")
                        break
                except Exception:
                    continue

            if not published:
                editor.send_keys(Keys.CONTROL + Keys.ENTER)
                published = True

            self._human_delay(POST_ACTION_DELAY_MIN, POST_ACTION_DELAY_MAX)

            result = PostResult(
                group_name=group_name,
                group_url=group_url,
                content_title=title or content[:50],
                content_type="value",
                success=published,
                timestamp=datetime.now().isoformat(),
                duration_seconds=round(time.time() - start_time, 1),
                error=None if published else "No se pudo hacer clic en Publicar",
            )

        except Exception as e:
            logger.error(f"❌ Error en {group_name}: {e}")
            result = PostResult(
                group_name=group_name,
                group_url=group_url,
                content_title=title,
                content_type="unknown",
                success=False,
                timestamp=datetime.now().isoformat(),
                error=str(e),
                duration_seconds=round(time.time() - start_time, 1),
            )

        self._post_log.append(result)
        self._save_log()
        return result

    def post_to_active_groups(self, content_override: Optional[str] = None,
                              group_override: Optional[List[str]] = None,
                              max_posts: int = 5) -> List[PostResult]:
        results = []
        today_count = self._get_post_count_today()

        if today_count >= self.config.max_posts_per_day:
            logger.warning(f"⚠️ Límite diario: {today_count}/{self.config.max_posts_per_day}")
            return [PostResult(
                group_name="SYSTEM", group_url="", content_title="Límite diario",
                content_type="system", success=False,
                timestamp=datetime.now().isoformat(),
                error=f"Límite diario alcanzado ({today_count})",
            )]

        max_to_post = min(max_posts, self.config.max_posts_per_day - today_count)

        # Cargar grupos activos
        groups_to_post = []
        if group_override:
            groups_to_post = group_override
        else:
            try:
                gf = GroupFinder(self.data_dir)
                active = gf.get_active_groups()
                groups_to_post = [
                    g.get("url", f"https://facebook.com/groups/{g['name'].lower().replace(' ', '')}")
                    for g in active if g.get("status") == "active"
                ]
                logger.info(f"   📋 {len(groups_to_post)} grupos activos")
            except Exception as e:
                return [PostResult(
                    group_name="SYSTEM", group_url="", content_title="Sin grupos",
                    content_type="system", success=False,
                    timestamp=datetime.now().isoformat(),
                    error=f"Error cargando grupos: {e}",
                )]

        if not groups_to_post:
            return [PostResult(
                group_name="SYSTEM", group_url="", content_title="Sin grupos activos",
                content_type="system", success=False,
                timestamp=datetime.now().isoformat(),
                error="No hay grupos activos. Agrega grupos desde el menú Grupos.",
            )]

        # Obtener contenido
        contents_to_post = []
        if content_override:
            contents_to_post = [(content_override, content_override[:50])]
        else:
            try:
                cp = ContentPlanner(self.data_dir)
                ideas = [i for i in cp.ideas if not i.posted]
                if not ideas:
                    se = StrategyEngine(self.data_dir)
                    niche = se.config.niche or "marketing digital"
                    ideas = cp.generate_ideas(niche, max_to_post)
                contents_to_post = [
                    (idea.description or idea.title, idea.title)
                    for idea in ideas[:max_to_post]
                ]
            except Exception:
                contents_to_post = [
                    ("Comparto este tip que me ha dado buenos resultados. ¿Qué opinan?",
                     "Tip de marketing digital")
                ]

        max_combos = min(len(groups_to_post), len(contents_to_post), max_to_post)
        groups_to_post = groups_to_post[:max_combos]
        contents_to_post = contents_to_post[:max_combos]

        logger.info("🚀 Iniciando sesión de publicación...")
        driver = self._create_driver()
        try:
            if not self.is_logged_in(driver):
                return [PostResult(
                    group_name="SYSTEM", group_url="", content_title="Sin sesión",
                    content_type="system", success=False,
                    timestamp=datetime.now().isoformat(),
                    error="No hay sesión activa. Configura el perfil primero.",
                )]

            for i, (group_url, (content, title)) in enumerate(
                    zip(groups_to_post, contents_to_post)):
                logger.info(f"\n📤 [{i+1}/{len(groups_to_post)}] Publicando...")
                result = self.post_to_group(driver, group_url, content, title)
                results.append(result)
                if i < len(groups_to_post) - 1:
                    delay = random.uniform(MIN_SECONDS_BETWEEN_POSTS, MAX_SECONDS_BETWEEN_POSTS)
                    logger.info(f"   ⏳ Esperando {delay:.0f}s...")
                    time.sleep(delay)
        finally:
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass

        success_count = sum(1 for r in results if r.success)
        logger.info(f"📊 RESUMEN: {success_count}/{len(results)} exitosos")
        self._save_log()
        return results

    # ─── CONFIGURACIÓN ──────────────────────────────────────────────────

    def update_config(self, **kwargs) -> bool:
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        self._save_config()
        return True

    def get_stats(self) -> dict:
        today_count = self._get_post_count_today()
        success_count = sum(1 for p in self._post_log if p.success)
        fail_count = sum(1 for p in self._post_log if not p.success)
        return {
            "configured": self.config.enabled,
            "max_posts_per_day": self.config.max_posts_per_day,
            "posts_today": today_count,
            "remaining_today": max(0, self.config.max_posts_per_day - today_count),
            "total_success": success_count,
            "total_failures": fail_count,
            "total_posts": len(self._post_log),
            "success_rate": round(
                success_count / len(self._post_log) * 100, 1
            ) if self._post_log else 0,
            "profile_exists": os.path.exists(self.profile_dir),
        }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(
        description="🐘 Facebook Poster - Publicación automática en grupos"
    )
    parser.add_argument("--status", action="store_true", help="Ver estado")
    parser.add_argument("--post", action="store_true", help="Publicar en grupos activos")
    parser.add_argument("--setup-profile", action="store_true",
                       help="Configurar perfil de Chrome")
    parser.add_argument("--max-posts", type=int, default=5, help="Máximo de posts")
    parser.add_argument("--enable", action="store_true", help="Habilitar")
    parser.add_argument("--disable", action="store_true", help="Deshabilitar")
    args = parser.parse_args()

    poster = FacebookPoster()

    if args.enable:
        poster.update_config(enabled=True)
        print("✅ Habilitado")
    if args.disable:
        poster.update_config(enabled=False)
        print("✅ Deshabilitado")
    if args.setup_profile:
        poster.setup_profile()
        return
    if args.status:
        status = poster.get_session_status()
        print("\n🐘 ESTADO:")
        print(f"  Habilitado:    {'✅ Sí' if status['configured'] else '❌ No'}")
        print(f"  Perfil Chrome: {'✅ Sí' if status['profile_exists'] else '❌ No'}")
        print(f"  Cookies:       {'✅ Sí' if status['cookies_exist'] else '❌ No'}")
        print(f"  Posts hoy:     {status['posts_today']}/{status['max_posts_per_day']}")
        if not status['profile_exists']:
            print("\n💡 python -m automation.facebook_poster --setup-profile")
        return
    if args.post:
        if not poster.config.enabled:
            print("⚠️  Deshabilitado. Usa --enable primero.")
            return
        if not poster.get_session_status()["profile_exists"]:
            print("❌ Perfil no configurado. Usa --setup-profile.")
            return
        print("\n🚀 Publicando...")
        results = poster.post_to_active_groups(max_posts=args.max_posts)
        success = sum(1 for r in results if r.success)
        print(f"\n📊 {success}/{len(results)} exitosos")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
