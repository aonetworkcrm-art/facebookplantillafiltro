"""
affiliate-ai-agent/agent/campaign.py
Campaign Manager.
Orchestrates the full affiliate campaign lifecycle.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json
import os

from .database import Database


@dataclass
class Campaign:
    """Represents a complete affiliate marketing campaign."""
    name: str
    product: str = ""
    product_url: str = ""
    commission: str = ""
    niche: str = ""
    target_audience: str = ""
    value_proposition: str = ""
    status: str = "draft"  # draft, setup, active, paused, completed
    sales_target: int = 10
    current_sales: int = 0
    revenue_target: float = 0.0
    current_revenue: float = 0.0
    investment: float = 0.0
    roi: float = 0.0
    start_date: str = ""
    end_date: str = ""
    notes: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Campaign":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class CampaignManager:
    """
    Manages multiple affiliate campaigns from creation to completion.
    Provides lifecycle management and performance tracking.
    """

    # Campaign lifecycle phases with descriptions
    LIFECYCLE = {
        "draft": "Borrador - Define los detalles básicos de la campaña",
        "setup": "Configuración - Prepara grupos, contenido y estrategia",
        "active": "Activa - Ejecutando la estrategia diariamente",
        "paused": "Pausada - Campaña detenida temporalmente",
        "completed": "Completada - Campaña finalizada con resultados"
    }

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db = Database(data_dir)
        self._campaigns: list[Campaign] = []
        self._load()

    def _load(self) -> None:
        data = self.db.load_campaigns()
        self._campaigns = [Campaign.from_dict(d) for d in data]

    def _save(self) -> None:
        self.db.save_campaigns([c.to_dict() for c in self._campaigns])

    @property
    def campaigns(self) -> list[Campaign]:
        return self._campaigns

    def create(self, name: str, product: str = "", niche: str = "",
               sales_target: int = 10) -> Campaign:
        """Create a new campaign."""
        campaign = Campaign(
            name=name,
            product=product,
            niche=niche,
            sales_target=sales_target,
            created_at=datetime.now().isoformat(),
            start_date=datetime.now().strftime("%Y-%m-%d")
        )
        self._campaigns.append(campaign)
        self._save()
        return campaign

    def get(self, name: str) -> Optional[Campaign]:
        """Get a campaign by name."""
        for c in self._campaigns:
            if c.name == name:
                return c
        return None

    def update(self, name: str, **kwargs) -> bool:
        """Update campaign fields."""
        campaign = self.get(name)
        if not campaign:
            return False
        for key, value in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        self._save()
        return True

    def delete(self, name: str) -> bool:
        """Delete a campaign."""
        for i, c in enumerate(self._campaigns):
            if c.name == name:
                del self._campaigns[i]
                self._save()
                return True
        return False

    def advance_status(self, name: str) -> bool:
        """Advance a campaign to the next lifecycle phase."""
        campaign = self.get(name)
        if not campaign:
            return False

        phases = ["draft", "setup", "active", "completed"]
        try:
            current_idx = phases.index(campaign.status)
            if current_idx < len(phases) - 1:
                campaign.status = phases[current_idx + 1]
                self._save()
                return True
        except ValueError:
            pass
        return False

    def record_sale(self, name: str, amount: float = 0.0) -> bool:
        """Record a sale for a campaign."""
        campaign = self.get(name)
        if not campaign:
            return False
        campaign.current_sales += 1
        campaign.current_revenue += amount
        if amount > 0 and campaign.investment > 0:
            campaign.roi = round(
                ((campaign.current_revenue - campaign.investment)
                 / campaign.investment) * 100, 1
            )
        self._save()
        return True

    def get_by_status(self, status: str) -> list[Campaign]:
        """Get campaigns by status."""
        return [c for c in self._campaigns if c.status == status]

    def get_summary(self) -> list[dict]:
        """Get a summary of all campaigns."""
        return [
            {
                "name": c.name,
                "product": c.product or "Sin definir",
                "niche": c.niche or "Sin definir",
                "status": c.status,
                "sales": f"{c.current_sales}/{c.sales_target}",
                "revenue": f"${c.current_revenue:.2f}",
                "roi": f"{c.roi}%" if c.roi else "N/A",
                "progress": round(
                    (c.current_sales / c.sales_target) * 100, 1
                ) if c.sales_target > 0 else 0
            }
            for c in self._campaigns
        ]

    def get_performance_report(self, name: str) -> Optional[dict]:
        """Get a detailed performance report for a campaign."""
        campaign = self.get(name)
        if not campaign:
            return None

        progress = (
            round((campaign.current_sales / campaign.sales_target) * 100, 1)
            if campaign.sales_target > 0 else 0
        )

        return {
            "name": campaign.name,
            "product": campaign.product,
            "niche": campaign.niche,
            "status": campaign.status,
            "status_description": self.LIFECYCLE.get(campaign.status, ""),
            "metrics": {
                "sales": {
                    "current": campaign.current_sales,
                    "target": campaign.sales_target,
                    "progress": progress
                },
                "revenue": {
                    "current": campaign.current_revenue,
                    "target": campaign.revenue_target
                },
                "investment": campaign.investment,
                "roi": campaign.roi
            },
            "timeline": {
                "start": campaign.start_date,
                "end": campaign.end_date or "En curso",
                "created": campaign.created_at
            },
            "value_proposition": campaign.value_proposition or "Sin definir"
        }
