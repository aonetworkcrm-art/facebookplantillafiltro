"""
affiliate-ai-agent/agent/lead_tracker.py
WhatsApp Lead Tracker.
Manages the conversion pipeline: lead capture → follow-up → close.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
import json
import os

from .database import Database


@dataclass
class Lead:
    """A lead captured through the WhatsApp funnel."""
    name: str
    phone: str
    source_group: str = ""
    source_post: str = ""
    product_interest: str = ""
    status: str = "new"  # new, contacted, meeting_set, interested, negotiation, closed, lost
    first_contact: str = ""
    last_contact: str = ""
    follow_up_count: int = 0
    notes: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Lead":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class LeadTracker:
    """
    Tracks leads from initial WhatsApp contact through to closing.
    Implements the WhatsApp conversion strategy from the video.
    """

    # Follow-up sequence (in days after last contact)
    FOLLOW_UP_SEQUENCE = [
        {"delay_days": 0, "type": "inicial", "message": "Primer contacto inicial"},
        {"delay_days": 1, "type": "seguimiento", "message": "¿Tuviste tiempo de revisar la info?"},
        {"delay_days": 3, "type": "valor", "message": "Compartir caso de éxito o testimonio"},
        {"delay_days": 7, "type": "urgencia", "message": "Recordatorio de oferta o plazo"},
        {"delay_days": 14, "type": "cierre", "message": "Último seguimiento antes de archivar"},
    ]

    # WhatsApp message templates for different stages
    MESSAGE_TEMPLATES = {
        "new": (
            "[nombre], ¡gracias por contactarme! 🚀\n\n"
            "Me alegra que estés interesado en [producto]. "
            "Cuéntame, ¿qué es lo que más te llama la atención de esto?"
        ),
        "interested": (
            "¡Qué bien [nombre]! Me da gusto que veas el potencial.\n\n"
            "Si te parece, te explico los detalles y cómo puedes empezar. "
            "¿Tienes 10 minutos para una llamada rápida o prefieres que te mande la info por aquí?"
        ),
        "follow_up_value": (
            "¡Hola [nombre]! 🙌\n\n"
            "Te comparto este caso de éxito de alguien que empezó como tú "
            "y logró [resultado] en solo [tiempo]. "
            "Me hizo pensar en ti porque [conexión_personal].\n\n"
            "¿Has estado pensando en [producto]?"
        ),
        "urgency": (
            "[nombre], quería avisarte que la oferta especial de [producto] "
            "termina en [plazo].\n\n"
            "No quiero que te quedes fuera. Si tienes alguna duda, "
            "aquí estoy para resolverla. 🤝"
        ),
        "last_follow_up": (
            "¡Hola [nombre]! 👋\n\n"
            "He intentado contactarte varias veces sin respuesta. "
            "Entiendo perfectamente si no es el momento.\n\n"
            "Si más adelante cambias de opinión, mi puerta siempre estará abierta. "
            "¡Mucho éxito en tus proyectos! 🌟"
        ),
        "closed": (
            "¡Felicidades [nombre]! 🎉\n\n"
            "Has tomado una excelente decisión. Bienvenido/a a [producto].\n\n"
            "Aquí estoy para lo que necesites durante tu proceso. "
            "¡Vamos a por tus resultados! 💪"
        ),
    }

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db = Database(data_dir)
        self._leads: list[Lead] = []
        self._load()

    def _load(self) -> None:
        data = self.db.load_leads()
        self._leads = [Lead.from_dict(d) for d in data]

    def _save(self) -> None:
        self.db.save_leads([l.to_dict() for l in self._leads])

    @property
    def leads(self) -> list[Lead]:
        return self._leads

    def add_lead(self, name: str, phone: str, source_group: str = "",
                 source_post: str = "", product_interest: str = "") -> Lead:
        """Register a new lead from WhatsApp."""
        now = datetime.now().isoformat()
        lead = Lead(
            name=name,
            phone=phone,
            source_group=source_group,
            source_post=source_post,
            product_interest=product_interest,
            created_at=now,
            first_contact=now
        )
        self._leads.append(lead)
        self._save()
        return lead

    def update_status(self, phone: str, new_status: str,
                      notes: str = "") -> bool:
        """Update a lead's status."""
        for lead in self._leads:
            if lead.phone == phone:
                lead.status = new_status
                lead.last_contact = datetime.now().isoformat()
                if notes:
                    lead.notes = notes
                self._save()
                return True
        return False

    def log_contact(self, phone: str) -> bool:
        """Log a contact/follow-up with a lead."""
        for lead in self._leads:
            if lead.phone == phone:
                lead.last_contact = datetime.now().isoformat()
                lead.follow_up_count += 1
                self._save()
                return True
        return False

    def get_leads_by_status(self, status: str) -> list[Lead]:
        """Get all leads in a given status."""
        return [l for l in self._leads if l.status == status]

    def get_leads_needing_followup(self) -> list[tuple[Lead, dict]]:
        """
        Get leads that need a follow-up, with the recommended message template.
        Based on the follow-up sequence timing.
        """
        now = datetime.now()
        needing = []

        for lead in self._leads:
            if lead.status in ("closed", "lost"):
                continue

            last = lead.last_contact or lead.created_at
            try:
                last_dt = datetime.fromisoformat(last)
            except (ValueError, TypeError):
                last_dt = now

            days_since = (now - last_dt).days
            next_step = None

            for step in self.FOLLOW_UP_SEQUENCE:
                if step["delay_days"] <= days_since:
                    next_step = step

            if next_step and lead.follow_up_count <= self.FOLLOW_UP_SEQUENCE.index(next_step):
                needing.append((lead, next_step))

        return needing

    def get_pipeline_summary(self) -> dict:
        """Get a summary of the lead pipeline (sales funnel)."""
        total = len(self._leads)
        return {
            "total": total,
            "new": len(self.get_leads_by_status("new")),
            "contacted": len(self.get_leads_by_status("contacted")),
            "meeting_set": len(self.get_leads_by_status("meeting_set")),
            "interested": len(self.get_leads_by_status("interested")),
            "negotiation": len(self.get_leads_by_status("negotiation")),
            "closed": len(self.get_leads_by_status("closed")),
            "lost": len(self.get_leads_by_status("lost")),
            "conversion_rate": round(
                len(self.get_leads_by_status("closed")) / total * 100, 1
            ) if total > 0 else 0,
            "follow_ups_today": len(self.get_leads_needing_followup())
        }

    def get_message_template(self, status: str, vars: dict = None) -> str:
        """Get a formatted message template for a given status."""
        template = self.MESSAGE_TEMPLATES.get(status, self.MESSAGE_TEMPLATES["new"])
        if vars:
            for key, value in vars.items():
                placeholder = f"[{key}]"
                template = template.replace(placeholder, value)
        return template

    def generate_waling_link(self, phone: str) -> str:
        """Generate a wa.me URL for a phone number.
        Formato correcto de WhatsApp: https://wa.me/584141234567
        (sin el signo +, solo código de país + número)
        """
        num = phone.replace("+", "").replace(" ", "").replace("-", "")
        return f"https://wa.me/{num}"

    def get_weekly_report(self) -> dict:
        """Generate a weekly lead report."""
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        new_this_week = 0
        closed_this_week = 0
        for lead in self._leads:
            try:
                created = datetime.fromisoformat(lead.created_at)
                if created >= week_ago:
                    new_this_week += 1
            except (ValueError, TypeError):
                pass
            if lead.status == "closed":
                try:
                    last = datetime.fromisoformat(lead.last_contact)
                    if last >= week_ago:
                        closed_this_week += 1
                except (ValueError, TypeError):
                    pass

        return {
            "new_this_week": new_this_week,
            "closed_this_week": closed_this_week,
            "pending_followups": len(self.get_leads_needing_followup()),
            "pipeline": self.get_pipeline_summary()
        }
