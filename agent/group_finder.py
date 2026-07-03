"""
affiliate-ai-agent/agent/group_finder.py
Group finding and filtering module.
Implements the group funnel: búsqueda estratégica, filtrado, y depuración.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json
import os

from .database import Database


@dataclass
class GroupProspect:
    """A potential Facebook group found during search."""
    name: str
    url: str = ""
    niche: str = ""
    member_count: int = 0
    posts_per_day: int = 0
    allows_promotion: Optional[bool] = None
    engagement_score: int = 0  # 0-100
    status: str = "discovered"  # discovered, pending_test, testing, active, rejected
    notes: str = ""
    discovered_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "GroupProspect":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class GroupFinder:
    """
    Manages the group discovery and filtering pipeline.
    Guides the user through finding, testing, and qualifying groups.
    """

    # Palabras clave para buscar grupos por nicho
    SEARCH_TEMPLATES = {
        "default": [
            "{niche} afiliados",
            "{niche} marketing",
            "{niche} negocios",
            "{niche} emprendimiento",
            "{niche} ventas",
            "marketing digital {niche}",
            "negocios online {niche}",
            "afiliados {niche}",
        ],
        "finanzas": [
            "inversiones",
            "libertad financiera",
            "ahorro e inversión",
            "trading",
            "criptomonedas",
        ],
        "salud": [
            "pérdida de peso",
            "fitness en casa",
            "alimentación saludable",
            "ejercicio sin gimnasio",
        ],
        "desarrollo_personal": [
            "productividad",
            "hábitos",
            "mentalidad ganadora",
            "coaching",
        ],
        "marketing": [
            "marketing digital",
            "publicidad online",
            "embudos de venta",
            "redes sociales",
        ],
    }

    # Señales de un grupo de calidad
    QUALITY_SIGNALS = {
        "positive": [
            "Publicaciones con varios comentarios",
            "El admin es activo",
            "Hay reglas claras",
            "Los miembros interactúan entre sí",
            "Se permite compartir contenido relevante",
        ],
        "negative": [
            "Solo spam y links sin contexto",
            "Publicaciones con 0 interacción",
            "Admin inactivo por meses",
            "Grupo lleno de bots",
            "Muchas reglas restrictivas",
        ]
    }

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db = Database(data_dir)
        self._prospects: list[GroupProspect] = []
        self._load()

    def _load(self) -> None:
        data = self.db.load_group_prospects()
        self._prospects = [GroupProspect.from_dict(d) for d in data]

    def _save(self) -> None:
        self.db.save_group_prospects([p.to_dict() for p in self._prospects])

    @property
    def prospects(self) -> list[GroupProspect]:
        return self._prospects

    def add_prospect(self, name: str, url: str = "", niche: str = "",
                     member_count: int = 0) -> GroupProspect:
        """Add a newly discovered group."""
        prospect = GroupProspect(
            name=name,
            url=url,
            niche=niche,
            member_count=member_count,
            discovered_at=datetime.now().isoformat()
        )
        self._prospects.append(prospect)
        self._save()
        return prospect

    def update_status(self, name: str, status: str,
                      allows_promotion: Optional[bool] = None,
                      engagement_score: Optional[int] = None,
                      notes: str = "") -> bool:
        """Update the status of a group after testing."""
        kwargs = {"status": status}
        if allows_promotion is not None:
            kwargs["allows_promotion"] = allows_promotion
        if engagement_score is not None:
            kwargs["engagement_score"] = min(100, max(0, engagement_score))
        if notes:
            kwargs["notes"] = notes
        result = self.db.update_group_prospect(name, **kwargs)
        if result:
            for p in self._prospects:
                if p.name == name:
                    if allows_promotion is not None:
                        p.allows_promotion = allows_promotion
                    if engagement_score is not None:
                        p.engagement_score = min(100, max(0, engagement_score))
                    p.status = status
                    if notes:
                        p.notes = notes
                    break
        return result

    def get_search_keywords(self, niche: str) -> list[str]:
        """Get relevant search keywords for a niche."""
        niche_lower = niche.lower().replace(" ", "_")
        for key, keywords in self.SEARCH_TEMPLATES.items():
            if key in niche_lower or niche_lower in key:
                return keywords
        return [t.format(niche=niche) for t in self.SEARCH_TEMPLATES["default"]]

    def get_groups_by_status(self, status: str) -> list[GroupProspect]:
        """Filter groups by their current status."""
        return [p for p in self._prospects if p.status == status]

    def get_pipeline_summary(self) -> dict:
        """Get a summary of the group pipeline."""
        return self.db.get_group_pipeline()

    def get_active_groups(self) -> list[GroupProspect]:
        """Get groups that are ready for posting."""
        return [p for p in self._prospects
                if p.status == "active" and p.allows_promotion is True]

    def get_quality_checklist(self) -> list[dict]:
        """Get a checklist for evaluating group quality."""
        return [
            {
                "criteria": "¿El grupo es activo? (publicaciones recientes)",
                "weight": "Alta"
            },
            {
                "criteria": "¿Las publicaciones tienen interacción real?",
                "weight": "Alta"
            },
            {
                "criteria": "¿El admin modera activamente?",
                "weight": "Media"
            },
            {
                "criteria": "¿Se permiten publicaciones promocionales?",
                "weight": "Crítica"
            },
            {
                "criteria": "¿El nicho del grupo es relevante?",
                "weight": "Alta"
            },
            {
                "criteria": "¿Hay competidores afiliados activos?",
                "weight": "Media"
            },
            {
                "criteria": "¿Los miembros son el público objetivo?",
                "weight": "Crítica"
            },
            {
                "criteria": "¿El tamaño del grupo es adecuado? (500-50K)",
                "weight": "Baja"
            }
        ]

    def suggest_next_actions(self) -> list[str]:
        """Suggest next actions based on current pipeline state."""
        actions = []
        discovered = self.get_groups_by_status("discovered")
        pending = self.get_groups_by_status("pending_test")
        testing = self.get_groups_by_status("testing")
        active = self.get_active_groups()

        if discovered:
            actions.append(f"Tienes {len(discovered)} grupos por evaluar. "
                           "Revisa sus reglas y decide si probarlos.")
        if pending:
            actions.append(f"Tienes {len(pending)} grupos pendientes de prueba. "
                           "Publica contenido de valor en ellos esta semana.")
        if testing:
            actions.append(f"{len(testing)} grupos en fase de prueba. "
                           "Monitorea el engagement en tus publicaciones.")
        if not active:
            actions.append("Aún no tienes grupos activos. "
                           "Concéntrate en descubrir y probar más grupos.")
        if active:
            actions.append(f"Tienes {len(active)} grupos activos. "
                           "Mantén la constancia en ellos.")

        if not actions:
            actions.append("Comienza buscando grupos relacionados a tu nicho "
                           "en Facebook. Únete a 20-30 grupos.")

        return actions
