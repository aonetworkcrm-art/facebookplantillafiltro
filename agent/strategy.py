"""
affiliate-ai-agent/agent/strategy.py
Core strategy engine based on the Hotmart Facebook Groups method.
Implements the 6-pillar strategy from the video.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional
import json
import os

from .database import Database


# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class Config:
    """Global agent configuration."""
    niche: str = ""
    fan_page_name: str = ""
    whatsapp_number: str = ""
    daily_posts: int = 3  # mañana, tarde, noche
    value_ratio: float = 0.8  # 80/20 rule
    data_dir: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Config":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Group:
    """A Facebook group for the campaign."""
    name: str
    url: str = ""
    niche: str = ""
    member_count: int = 0
    allows_posts: Optional[bool] = None  # None = untested
    engagement_level: str = "unknown"  # high, medium, low, unknown
    notes: str = ""
    added_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Group":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ContentItem:
    """A piece of content for the 80/20 plan."""
    title: str
    content_type: str = "value"  # "value" or "promotion"
    body: str = ""
    platform: str = "facebook_group"
    scheduled_date: str = ""
    posted: bool = False
    group_name: str = ""
    engagement_notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ContentItem":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Lead:
    """A lead captured via WhatsApp."""
    name: str = ""
    phone: str = ""
    source_group: str = ""
    interest: str = ""
    status: str = "new"  # new, contacted, interested, closed, lost
    contacted_at: str = ""
    notes: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Lead":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Campaign:
    """A complete affiliate campaign."""
    name: str
    product: str = ""
    product_url: str = ""
    commission: str = ""
    niche: str = ""
    groups: list = field(default_factory=list)
    content_plan: list = field(default_factory=list)
    leads: list = field(default_factory=list)
    status: str = "draft"  # draft, active, paused, completed
    created_at: str = ""
    target_sales: int = 0
    current_sales: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Campaign":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ─── Data Persistence ────────────────────────────────────────────────────────

class DataStore:
    """SQLite-based data store using the central Database class."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db = Database(data_dir)

    def save(self, key: str, data: any) -> None:
        if key == "config" and isinstance(data, dict):
            self.db.save_config(data)
        elif key == "campaigns" and isinstance(data, list):
            self.db.save_campaigns(data)
        elif key == "group_prospects" and isinstance(data, list):
            self.db.save_group_prospects(data)
        elif key == "content_ideas" and isinstance(data, list):
            self.db.save_content_ideas(data)
        elif key == "leads" and isinstance(data, list):
            self.db.save_leads(data)
        else:
            # Generic fallback: store as JSON in a custom table
            conn = self.db._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (f"_json_{key}", json.dumps(data, ensure_ascii=False))
            )
            conn.commit()

    def load(self, key: str, default: any = None) -> any:
        if key == "config":
            return self.db.load_config()
        elif key == "campaigns":
            return self.db.load_campaigns()
        elif key == "group_prospects":
            return self.db.load_group_prospects()
        elif key == "content_ideas":
            return self.db.load_content_ideas()
        elif key == "leads":
            return self.db.load_leads()
        elif key == "routine_log":
            return self.db.load_routine_log()
        else:
            conn = self.db._get_conn()
            row = conn.execute(
                "SELECT value FROM config WHERE key = ?", (f"_json_{key}",)
            ).fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except (json.JSONDecodeError, TypeError):
                    return row["value"]
            return default if default is not None else {}


# ─── Strategy Engine ─────────────────────────────────────────────────────────

class StrategyEngine:
    """
    The core engine that implements the 6-pillar Hotmart strategy.
    Guides the user through: autoridad, fan pages, group filtering,
    80/20 content, WhatsApp conversion, y constancia diaria.
    """

    PILLARS = [
        {
            "id": 1,
            "name": "Fundamentos y Autoridad",
            "description": "Posiciónate como autoridad sin desesperación. Aprende psicología de venta.",
            "icon": "🎯"
        },
        {
            "id": 2,
            "name": "Fan Page Profesional",
            "description": "Crea una Fan Page en lugar de usar tu perfil personal.",
            "icon": "📄"
        },
        {
            "id": 3,
            "name": "Embudo de Grupos",
            "description": "Filtra y selecciona los grupos adecuados para tu nicho.",
            "icon": "🔍"
        },
        {
            "id": 4,
            "name": "Contenido 80/20",
            "description": "80% valor, 20% promoción. Construye confianza antes de vender.",
            "icon": "📊"
        },
        {
            "id": 5,
            "name": "Conversión WhatsApp",
            "description": "Usa enlaces waling para capturar leads y cerrar ventas.",
            "icon": "💬"
        },
        {
            "id": 6,
            "name": "Acción y Constancia",
            "description": "Interacción diaria: mañana, tarde y noche. Sin spam.",
            "icon": "⚡"
        }
    ]

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
        self.store = DataStore(data_dir)
        self.config = self._load_config()
        self.campaigns: list[Campaign] = []
        self._load_campaigns()

    def _load_config(self) -> Config:
        data = self.store.load("config", {})
        return Config.from_dict(data) if data else Config()

    def save_config(self) -> None:
        self.store.save("config", self.config.to_dict())

    def _load_campaigns(self) -> None:
        data = self.store.load("campaigns", [])
        self.campaigns = [Campaign.from_dict(c) for c in data]

    def save_campaigns(self) -> None:
        self.store.save("campaigns", [c.to_dict() for c in self.campaigns])

    # ─── Config ───────────────────────────────────────────────────────────

    def update_config(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        self.save_config()

    def is_configured(self) -> bool:
        return bool(self.config.niche)

    # ─── Campaigns ────────────────────────────────────────────────────────

    def create_campaign(self, name: str, product: str = "",
                        product_url: str = "", niche: str = "",
                        target_sales: int = 0) -> Campaign:
        campaign = Campaign(
            name=name,
            product=product,
            product_url=product_url,
            niche=niche or self.config.niche,
            target_sales=target_sales,
            created_at=datetime.now().isoformat()
        )
        self.campaigns.append(campaign)
        self.save_campaigns()
        return campaign

    def get_campaign(self, name: str) -> Optional[Campaign]:
        for c in self.campaigns:
            if c.name == name:
                return c
        return None

    def delete_campaign(self, name: str) -> bool:
        for i, c in enumerate(self.campaigns):
            if c.name == name:
                del self.campaigns[i]
                self.save_campaigns()
                return True
        return False

    # ─── Groups ───────────────────────────────────────────────────────────

    def add_group(self, campaign_name: str, group: Group) -> bool:
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return False
        campaign.groups.append(group.to_dict())
        self.save_campaigns()
        return True

    def remove_group(self, campaign_name: str, group_name: str) -> bool:
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return False
        campaign.groups = [g for g in campaign.groups if g.get("name") != group_name]
        self.save_campaigns()
        return True

    def get_groups_summary(self, campaign_name: str) -> dict:
        """Returns a summary of groups for a campaign."""
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return {"total": 0, "allowed": 0, "blocked": 0, "untested": 0}
        groups = campaign.groups
        total = len(groups)
        allowed = sum(1 for g in groups if g.get("allows_posts") is True)
        blocked = sum(1 for g in groups if g.get("allows_posts") is False)
        untested = sum(1 for g in groups if g.get("allows_posts") is None)
        return {
            "total": total,
            "allowed": allowed,
            "blocked": blocked,
            "untested": untested
        }

    # ─── Content Planning ─────────────────────────────────────────────────

    def add_content(self, campaign_name: str, item: ContentItem) -> bool:
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return False
        campaign.content_plan.append(item.to_dict())
        self.save_campaigns()
        return True

    def get_content_stats(self, campaign_name: str) -> dict:
        """Returns 80/20 compliance stats."""
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return {"total": 0, "value": 0, "promotion": 0, "ratio": 0}

        items = campaign.content_plan
        total = len(items)
        value = sum(1 for i in items if i.get("content_type") == "value")
        promotion = sum(1 for i in items if i.get("content_type") == "promotion")
        ratio = value / total if total > 0 else 0
        return {
            "total": total,
            "value": value,
            "promotion": promotion,
            "ratio": round(ratio, 2),
            "target_ratio": 0.8,
            "compliant": ratio >= 0.8
        }

    # ─── Leads ────────────────────────────────────────────────────────────

    def add_lead(self, campaign_name: str, lead: Lead) -> bool:
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return False
        campaign.leads.append(lead.to_dict())
        self.save_campaigns()
        return True

    def update_lead_status(self, campaign_name: str, phone: str,
                           status: str) -> bool:
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return False
        for lead in campaign.leads:
            if lead.get("phone") == phone:
                lead["status"] = status
                lead["contacted_at"] = datetime.now().isoformat()
                self.save_campaigns()
                return True
        return False

    def get_lead_stats(self, campaign_name: str) -> dict:
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return {"total": 0, "new": 0, "contacted": 0,
                    "interested": 0, "closed": 0, "lost": 0}
        leads = campaign.leads
        return {
            "total": len(leads),
            "new": sum(1 for l in leads if l.get("status") == "new"),
            "contacted": sum(1 for l in leads if l.get("status") == "contacted"),
            "interested": sum(1 for l in leads if l.get("status") == "interested"),
            "closed": sum(1 for l in leads if l.get("status") == "closed"),
            "lost": sum(1 for l in leads if l.get("status") == "lost")
        }

    # ─── Strategy Guidance ───────────────────────────────────────────────

    def get_pillar_guidance(self, pillar_id: int) -> dict:
        """Get detailed guidance for a specific pillar."""
        pillar = next((p for p in self.PILLARS if p["id"] == pillar_id), None)
        if not pillar:
            return {}

        guidance = {
            1: {
                "steps": [
                    "Define tu nicho de mercado específico",
                    "Investiga los problemas y deseos de tu audiencia",
                    "Crea contenido que demuestre expertise sin vender",
                    "Desarrolla habilidades de persuasión y comunicación",
                    "Estudia a la competencia exitosa en tu nicho"
                ],
                "warning": "No caigas en la desesperación por vender. La autoridad se construye con tiempo."
            },
            2: {
                "steps": [
                    "Crea una Fan Page con nombre profesional relacionado a tu nicho",
                    "Diseña un logo y portada profesional (usa Canva)",
                    "Completa toda la información de la página",
                    "Publica 5-10 posts de valor antes de promocionar",
                    "Invita a amigos y conocidos a dar like"
                ],
                "warning": "Nunca uses tu perfil personal para promocionar. La Fan Page te protege."
            },
            3: {
                "steps": [
                    "Busca grupos en Facebook relacionados a tu nicho",
                    "Usa palabras clave: 'afiliados', 'negocios', 'emprendimiento' + tu nicho",
                    "Únete a 20-30 grupos como mínimo",
                    "Observa las reglas de cada grupo (¿permiten publicaciones?)",
                    "Publica contenido de valor primero en cada grupo",
                    "Filtra: quédate solo con los que permiten posts y tienen interacción"
                ],
                "warning": "No publiques en todos los grupos a la vez. Prueba cada grupo con contenido de valor primero."
            },
            4: {
                "steps": [
                    "Planifica 10 contenidos: 8 de valor, 2 promocionales",
                    "Contenido de valor: tips, tutoriales, casos de éxito, tendencias",
                    "Contenido promocional: reseñas honestas, comparativas, ofertas",
                    "Usa un calendario semanal para organizar las publicaciones",
                    "Mide el engagement de cada tipo de contenido"
                ],
                "warning": "Si solo promocionas, la comunidad te rechazará. Respeta el 80/20."
            },
            5: {
                "steps": [
                    "Configura tu número de WhatsApp Business",
                    "Genera enlaces waling: https://wa.link/tu-numero",
                    "Incluye el enlace en tu biografía de la Fan Page",
                    "En posts promocionales: 'Comenta 'INFO' y te envío detalles por WhatsApp'",
                    "Prepara un guión de ventas para la conversación de WhatsApp",
                    "Da seguimiento personalizado a cada lead"
                ],
                "warning": "No envíes spam por WhatsApp. Cada lead merece atención personalizada."
            },
            6: {
                "steps": [
                    "Establece 3 momentos de interacción: mañana, tarde, noche",
                    "Mañana: comparte contenido de valor en 3-5 grupos",
                    "Tarde: responde comentarios e interactúa en los grupos",
                    "Noche: revisa métricas y planea el día siguiente",
                    "Mantén constancia por 21 días para crear el hábito"
                ],
                "warning": "La clave no es la intensidad, es la constancia. Mejor poco todos los días."
            }
        }
        return {
            "pillar": pillar,
            "guidance": guidance.get(pillar_id, {})
        }

    def get_weekly_schedule(self) -> list:
        """Generate a weekly content schedule template."""
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        schedule = []
        for day in days:
            schedule.append({
                "day": day,
                "morning": "📝 Publicar contenido de valor en grupos",
                "afternoon": "💬 Interactuar y responder comentarios",
                "night": "📊 Revisar métricas y planificar"
            })
        return schedule

    def get_waling_link(self) -> str:
        """Generate a wa.link link for the configured number."""
        if not self.config.whatsapp_number:
            return ""
        num = self.config.whatsapp_number.replace("+", "").replace(" ", "")
        return f"https://wa.link/{num}"

    def export_campaign_report(self, campaign_name: str) -> dict:
        """Export a full campaign report."""
        campaign = self.get_campaign(campaign_name)
        if not campaign:
            return {"error": "Campaign not found"}

        groups_summary = self.get_groups_summary(campaign_name)
        content_stats = self.get_content_stats(campaign_name)
        lead_stats = self.get_lead_stats(campaign_name)

        return {
            "campaign": campaign.name,
            "product": campaign.product,
            "niche": campaign.niche,
            "status": campaign.status,
            "created_at": campaign.created_at,
            "target_sales": campaign.target_sales,
            "current_sales": campaign.current_sales,
            "groups": groups_summary,
            "content": content_stats,
            "leads": lead_stats,
            "config": self.config.to_dict()
        }
