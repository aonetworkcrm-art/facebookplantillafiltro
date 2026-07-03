"""
affiliate-ai-agent/agent/database.py
Central SQLite database module.
Replaces all JSON file storage with a single ACID-compliant SQLite database.
Includes automatic migration from legacy JSON files.
"""

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional, Any


# ─── Schema Definitions ─────────────────────────────────────────────────────

SCHEMA = {
    "config": """
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """,
    "campaigns": """
        CREATE TABLE IF NOT EXISTS campaigns (
            name TEXT PRIMARY KEY,
            product TEXT DEFAULT '',
            product_url TEXT DEFAULT '',
            commission TEXT DEFAULT '',
            niche TEXT DEFAULT '',
            target_audience TEXT DEFAULT '',
            value_proposition TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            sales_target INTEGER DEFAULT 10,
            current_sales INTEGER DEFAULT 0,
            revenue_target REAL DEFAULT 0.0,
            current_revenue REAL DEFAULT 0.0,
            investment REAL DEFAULT 0.0,
            roi REAL DEFAULT 0.0,
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
    "campaign_groups": """
        CREATE TABLE IF NOT EXISTS campaign_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT DEFAULT '',
            niche TEXT DEFAULT '',
            member_count INTEGER DEFAULT 0,
            allows_posts INTEGER,
            engagement_level TEXT DEFAULT 'unknown',
            notes TEXT DEFAULT '',
            added_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (campaign_name) REFERENCES campaigns(name) ON DELETE CASCADE
        )
    """,
    "campaign_content": """
        CREATE TABLE IF NOT EXISTS campaign_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            title TEXT NOT NULL,
            content_type TEXT DEFAULT 'value',
            body TEXT DEFAULT '',
            category TEXT DEFAULT '',
            description TEXT DEFAULT '',
            platform TEXT DEFAULT 'facebook_group',
            scheduled_date TEXT DEFAULT '',
            posted INTEGER DEFAULT 0,
            group_name TEXT DEFAULT '',
            engagement_notes TEXT DEFAULT '',
            engagement_result TEXT DEFAULT '',
            target_group TEXT DEFAULT '',
            FOREIGN KEY (campaign_name) REFERENCES campaigns(name) ON DELETE CASCADE
        )
    """,
    "campaign_leads": """
        CREATE TABLE IF NOT EXISTS campaign_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            source_group TEXT DEFAULT '',
            source_post TEXT DEFAULT '',
            interest TEXT DEFAULT '',
            product_interest TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            first_contact TEXT DEFAULT '',
            last_contact TEXT DEFAULT '',
            contacted_at TEXT DEFAULT '',
            follow_up_count INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (campaign_name) REFERENCES campaigns(name) ON DELETE CASCADE
        )
    """,
    "group_prospects": """
        CREATE TABLE IF NOT EXISTS group_prospects (
            name TEXT PRIMARY KEY,
            url TEXT DEFAULT '',
            niche TEXT DEFAULT '',
            member_count INTEGER DEFAULT 0,
            posts_per_day INTEGER DEFAULT 0,
            allows_promotion INTEGER,
            engagement_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'discovered',
            notes TEXT DEFAULT '',
            discovered_at TEXT DEFAULT (datetime('now'))
        )
    """,
    "content_ideas": """
        CREATE TABLE IF NOT EXISTS content_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content_type TEXT DEFAULT 'value',
            category TEXT DEFAULT '',
            description TEXT DEFAULT '',
            target_group TEXT DEFAULT '',
            scheduled_date TEXT DEFAULT '',
            posted INTEGER DEFAULT 0,
            engagement_result TEXT DEFAULT ''
        )
    """,
    "leads": """
        CREATE TABLE IF NOT EXISTS leads (
            phone TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source_group TEXT DEFAULT '',
            source_post TEXT DEFAULT '',
            product_interest TEXT DEFAULT '',
            status TEXT DEFAULT 'new',
            first_contact TEXT DEFAULT '',
            last_contact TEXT DEFAULT '',
            contacted_at TEXT DEFAULT '',
            follow_up_count INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
    "routine_log": """
        CREATE TABLE IF NOT EXISTS routine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            period TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            tasks TEXT DEFAULT '[]'
        )
    """,
}

# Indexes for performance
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_campaign_groups_campaign ON campaign_groups(campaign_name)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_content_campaign ON campaign_content(campaign_name)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_content_type ON campaign_content(content_type)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_content_scheduled ON campaign_content(scheduled_date)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_leads_campaign ON campaign_leads(campaign_name)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_leads_status ON campaign_leads(status)",
    "CREATE INDEX IF NOT EXISTS idx_group_prospects_status ON group_prospects(status)",
    "CREATE INDEX IF NOT EXISTS idx_content_ideas_type ON content_ideas(content_type)",
    "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
    "CREATE INDEX IF NOT EXISTS idx_routine_log_date ON routine_log(date)",
]


# ─── Database Connection Manager ────────────────────────────────────────────

class Database:
    """
    Central SQLite database with thread-safe connection management.
    Provides a dict-like interface for backward compatibility with JSON stores.

    Usage:
        db = Database()
        db.save_config({"niche": "finanzas"})
        config = db.load_config()
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.db_path = os.path.join(data_dir, "affiliate_agent.db")
        self._local = threading.local()
        self._init_db()
        self._migrate_from_json()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_db(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = self._get_conn()
        for name, ddl in SCHEMA.items():
            conn.execute(ddl)
        for idx in INDEXES:
            conn.execute(idx)
        conn.commit()

    # ─── JSON Migration ─────────────────────────────────────────────────

    def _migrate_from_json(self) -> None:
        """Migrate data from legacy JSON files to SQLite."""
        json_files = {
            "config": os.path.join(self.data_dir, "config.json"),
            "campaign_groups": os.path.join(self.data_dir, "group_prospects.json"),
            "content_ideas": os.path.join(self.data_dir, "content_ideas.json"),
            "leads": os.path.join(self.data_dir, "leads.json"),
            "campaigns": os.path.join(self.data_dir, "campaigns.json"),
            "routine_log": os.path.join(self.data_dir, "routine_log.json"),
        }

        for key, path in json_files.items():
            if os.path.exists(path):
                try:
                    self._migrate_file(key, path)
                    # Rename migrated files to .bak
                    os.rename(path, path + ".bak")
                except Exception as e:
                    print(f"⚠️  Migration warning for {key}: {e}")

    def _migrate_file(self, key: str, path: str) -> None:
        """Migrate a single JSON file to the database."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        conn = self._get_conn()

        if key == "config" and isinstance(data, dict):
            for k, v in data.items():
                val = json.dumps(v) if not isinstance(v, str) else v
                conn.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    (k, str(val))
                )

        elif key == "campaign_groups" and isinstance(data, list):
            for item in data:
                conn.execute("""
                    INSERT OR IGNORE INTO group_prospects
                        (name, url, niche, member_count, engagement_score, status, notes, discovered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("name", ""),
                    item.get("url", ""),
                    item.get("niche", ""),
                    item.get("member_count", 0),
                    item.get("engagement_score", 0),
                    item.get("status", "discovered"),
                    item.get("notes", ""),
                    item.get("discovered_at", datetime.now().isoformat())
                ))

        elif key == "content_ideas" and isinstance(data, list):
            for item in data:
                conn.execute("""
                    INSERT INTO content_ideas
                        (title, content_type, category, description, target_group,
                         scheduled_date, posted, engagement_result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("title", ""),
                    item.get("content_type", "value"),
                    item.get("category", ""),
                    item.get("description", ""),
                    item.get("target_group", ""),
                    item.get("scheduled_date", ""),
                    1 if item.get("posted") else 0,
                    item.get("engagement_result", "")
                ))

        elif key == "leads" and isinstance(data, list):
            for item in data:
                conn.execute("""
                    INSERT OR IGNORE INTO leads
                        (phone, name, source_group, source_post, product_interest,
                         status, first_contact, last_contact, follow_up_count, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("phone", ""),
                    item.get("name", ""),
                    item.get("source_group", ""),
                    item.get("source_post", ""),
                    item.get("product_interest", ""),
                    item.get("status", "new"),
                    item.get("first_contact", ""),
                    item.get("last_contact", ""),
                    item.get("follow_up_count", 0),
                    item.get("notes", ""),
                    item.get("created_at", datetime.now().isoformat())
                ))

        elif key == "campaigns" and isinstance(data, list):
            for c in data:
                # Insert campaign
                conn.execute("""
                    INSERT OR IGNORE INTO campaigns
                        (name, product, product_url, commission, niche, status,
                         sales_target, current_sales, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c.get("name", ""),
                    c.get("product", ""),
                    c.get("product_url", ""),
                    c.get("commission", ""),
                    c.get("niche", ""),
                    c.get("status", "draft"),
                    c.get("target_sales", c.get("sales_target", 10)),
                    c.get("current_sales", 0),
                    c.get("created_at", datetime.now().isoformat())
                ))

                # Migrate groups embedded in campaigns
                for g in c.get("groups", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO campaign_groups
                            (campaign_name, name, url, niche, member_count,
                             allows_posts, engagement_level, notes, added_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        c.get("name", ""),
                        g.get("name", ""),
                        g.get("url", ""),
                        g.get("niche", ""),
                        g.get("member_count", 0),
                        1 if g.get("allows_posts") else 0 if g.get("allows_posts") is False else None,
                        g.get("engagement_level", "unknown"),
                        g.get("notes", ""),
                        g.get("added_at", datetime.now().isoformat())
                    ))

                # Migrate content embedded in campaigns
                for ci in c.get("content_plan", []):
                    conn.execute("""
                        INSERT INTO campaign_content
                            (campaign_name, title, content_type, body, platform,
                             scheduled_date, posted, group_name, engagement_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        c.get("name", ""),
                        ci.get("title", ""),
                        ci.get("content_type", "value"),
                        ci.get("body", ""),
                        ci.get("platform", "facebook_group"),
                        ci.get("scheduled_date", ""),
                        1 if ci.get("posted") else 0,
                        ci.get("group_name", ""),
                        ci.get("engagement_notes", "")
                    ))

                # Migrate leads embedded in campaigns
                for l in c.get("leads", []):
                    conn.execute("""
                        INSERT OR IGNORE INTO campaign_leads
                            (campaign_name, name, phone, source_group, interest,
                             status, contacted_at, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        c.get("name", ""),
                        l.get("name", ""),
                        l.get("phone", ""),
                        l.get("source_group", ""),
                        l.get("interest", ""),
                        l.get("status", "new"),
                        l.get("contacted_at", ""),
                        l.get("notes", ""),
                        l.get("created_at", datetime.now().isoformat())
                    ))

        elif key == "routine_log" and isinstance(data, dict):
            for date_str, periods in data.items():
                for period, info in periods.items():
                    tasks = json.dumps(info.get("tasks", []))
                    conn.execute("""
                        INSERT OR IGNORE INTO routine_log (date, period, completed_at, tasks)
                        VALUES (?, ?, ?, ?)
                    """, (
                        date_str,
                        period,
                        info.get("completed_at", datetime.now().isoformat()),
                        tasks
                    ))

        conn.commit()

    # ─── Config ─────────────────────────────────────────────────────────

    def save_config(self, config_dict: dict) -> None:
        """Save configuration as key-value pairs."""
        conn = self._get_conn()
        for k, v in config_dict.items():
            val = json.dumps(v) if not isinstance(v, str) else str(v)
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (k, val)
            )
        conn.commit()

    def load_config(self) -> dict:
        """Load configuration as dict."""
        conn = self._get_conn()
        rows = conn.execute("SELECT key, value FROM config").fetchall()
        result = {}
        for row in rows:
            # Try parsing as JSON for complex values
            try:
                result[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                result[row["key"]] = row["value"]
        return result

    # ─── Campaigns ──────────────────────────────────────────────────────

    def save_campaigns(self, campaigns: list[dict]) -> None:
        """Save all campaigns (replaces full list)."""
        conn = self._get_conn()
        conn.execute("DELETE FROM campaigns")
        for c in campaigns:
            conn.execute("""
                INSERT INTO campaigns
                    (name, product, product_url, commission, niche, target_audience,
                     value_proposition, status, sales_target, current_sales,
                     revenue_target, current_revenue, investment, roi,
                     start_date, end_date, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get("name", ""),
                c.get("product", ""),
                c.get("product_url", ""),
                c.get("commission", ""),
                c.get("niche", ""),
                c.get("target_audience", ""),
                c.get("value_proposition", ""),
                c.get("status", "draft"),
                c.get("target_sales", c.get("sales_target", 10)),
                c.get("current_sales", 0),
                c.get("revenue_target", 0.0),
                c.get("current_revenue", 0.0),
                c.get("investment", 0.0),
                c.get("roi", 0.0),
                c.get("start_date", ""),
                c.get("end_date", ""),
                c.get("notes", ""),
                c.get("created_at", datetime.now().isoformat())
            ))
            # Save embedded groups
            for g in c.get("groups", []):
                self._save_campaign_group(conn, c["name"], g)
            # Save embedded content
            for ci in c.get("content_plan", []):
                self._save_campaign_content(conn, c["name"], ci)
            # Save embedded leads
            for l in c.get("leads", []):
                self._save_campaign_lead(conn, c["name"], l)
        conn.commit()

    def load_campaigns(self) -> list[dict]:
        """Load all campaigns with embedded data."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
        campaigns = []
        for row in rows:
            c = dict(row)
            name = c["name"]
            # Load embedded groups
            groups = conn.execute(
                "SELECT * FROM campaign_groups WHERE campaign_name = ?", (name,)
            ).fetchall()
            c["groups"] = [dict(g) for g in groups]
            # Load embedded content
            content = conn.execute(
                "SELECT * FROM campaign_content WHERE campaign_name = ?", (name,)
            ).fetchall()
            c["content_plan"] = [dict(ci) for ci in content]
            # Load embedded leads
            leads = conn.execute(
                "SELECT * FROM campaign_leads WHERE campaign_name = ?", (name,)
            ).fetchall()
            c["leads"] = [dict(l) for l in leads]
            campaigns.append(c)
        return campaigns

    def _save_campaign_group(self, conn, campaign_name: str, g: dict) -> None:
        conn.execute("""
            INSERT INTO campaign_groups
                (campaign_name, name, url, niche, member_count,
                 allows_posts, engagement_level, notes, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_name,
            g.get("name", ""),
            g.get("url", ""),
            g.get("niche", ""),
            g.get("member_count", 0),
            1 if g.get("allows_posts") else 0 if g.get("allows_posts") is False else None,
            g.get("engagement_level", "unknown"),
            g.get("notes", ""),
            g.get("added_at", datetime.now().isoformat())
        ))

    def _save_campaign_content(self, conn, campaign_name: str, ci: dict) -> None:
        conn.execute("""
            INSERT INTO campaign_content
                (campaign_name, title, content_type, body, platform,
                 scheduled_date, posted, group_name, engagement_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_name,
            ci.get("title", ""),
            ci.get("content_type", "value"),
            ci.get("body", ""),
            ci.get("platform", "facebook_group"),
            ci.get("scheduled_date", ""),
            1 if ci.get("posted") else 0,
            ci.get("group_name", ""),
            ci.get("engagement_notes", "")
        ))

    def _save_campaign_lead(self, conn, campaign_name: str, l: dict) -> None:
        conn.execute("""
            INSERT INTO campaign_leads
                (campaign_name, name, phone, source_group, interest,
                 status, contacted_at, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_name,
            l.get("name", ""),
            l.get("phone", ""),
            l.get("source_group", ""),
            l.get("interest", ""),
            l.get("status", "new"),
            l.get("contacted_at", ""),
            l.get("notes", ""),
            l.get("created_at", datetime.now().isoformat())
        ))

    # ─── Group Prospects ────────────────────────────────────────────────

    def save_group_prospects(self, prospects: list[dict]) -> None:
        """Save all group prospects."""
        conn = self._get_conn()
        conn.execute("DELETE FROM group_prospects")
        for p in prospects:
            conn.execute("""
                INSERT INTO group_prospects
                    (name, url, niche, member_count, posts_per_day,
                     allows_promotion, engagement_score, status, notes, discovered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p.get("name", ""),
                p.get("url", ""),
                p.get("niche", ""),
                p.get("member_count", 0),
                p.get("posts_per_day", 0),
                1 if p.get("allows_promotion") else 0 if p.get("allows_promotion") is False else None,
                p.get("engagement_score", 0),
                p.get("status", "discovered"),
                p.get("notes", ""),
                p.get("discovered_at", datetime.now().isoformat())
            ))
        conn.commit()

    def load_group_prospects(self) -> list[dict]:
        """Load all group prospects."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM group_prospects ORDER BY discovered_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update_group_prospect(self, name: str, **kwargs) -> bool:
        """Update a single group prospect."""
        conn = self._get_conn()
        fields = []
        values = []
        for k, v in kwargs.items():
            if k in ("allows_promotion",):
                v = 1 if v else 0 if v is False else None
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(name)
        if fields:
            cursor = conn.execute(
                f"UPDATE group_prospects SET {', '.join(fields)} WHERE name = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
        return False

    # ─── Content Ideas ──────────────────────────────────────────────────

    def save_content_ideas(self, ideas: list[dict]) -> None:
        """Save all content ideas."""
        conn = self._get_conn()
        conn.execute("DELETE FROM content_ideas")
        for idea in ideas:
            conn.execute("""
                INSERT INTO content_ideas
                    (title, content_type, category, description, target_group,
                     scheduled_date, posted, engagement_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                idea.get("title", ""),
                idea.get("content_type", "value"),
                idea.get("category", ""),
                idea.get("description", ""),
                idea.get("target_group", ""),
                idea.get("scheduled_date", ""),
                1 if idea.get("posted") else 0,
                idea.get("engagement_result", "")
            ))
        conn.commit()

    def load_content_ideas(self) -> list[dict]:
        """Load all content ideas."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM content_ideas ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def update_content_idea(self, title: str, **kwargs) -> bool:
        """Update a content idea by title."""
        conn = self._get_conn()
        fields = []
        values = []
        for k, v in kwargs.items():
            if k == "posted":
                v = 1 if v else 0
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(title)
        if fields:
            cursor = conn.execute(
                f"UPDATE content_ideas SET {', '.join(fields)} WHERE title = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
        return False

    # ─── Leads ──────────────────────────────────────────────────────────

    def save_leads(self, leads: list[dict]) -> None:
        """Save all leads."""
        conn = self._get_conn()
        conn.execute("DELETE FROM leads")
        for lead in leads:
            conn.execute("""
                INSERT INTO leads
                    (phone, name, source_group, source_post, product_interest,
                     status, first_contact, last_contact, follow_up_count,
                     notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.get("phone", ""),
                lead.get("name", ""),
                lead.get("source_group", ""),
                lead.get("source_post", ""),
                lead.get("product_interest", ""),
                lead.get("status", "new"),
                lead.get("first_contact", ""),
                lead.get("last_contact", ""),
                lead.get("follow_up_count", 0),
                lead.get("notes", ""),
                lead.get("created_at", datetime.now().isoformat())
            ))
        conn.commit()

    def load_leads(self) -> list[dict]:
        """Load all leads."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update_lead(self, phone: str, **kwargs) -> bool:
        """Update a lead by phone."""
        conn = self._get_conn()
        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(phone)
        if fields:
            cursor = conn.execute(
                f"UPDATE leads SET {', '.join(fields)} WHERE phone = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0
        return False

    # ─── Routine Log ────────────────────────────────────────────────────

    def save_routine_entry(self, date_str: str, period: str,
                           completed_at: str, tasks: list) -> None:
        """Save a routine log entry."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO routine_log (date, period, completed_at, tasks)
            VALUES (?, ?, ?, ?)
        """, (date_str, period, completed_at, json.dumps(tasks)))
        conn.commit()

    def load_routine_log(self) -> dict:
        """Load routine log as dict (for backward compatibility)."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM routine_log ORDER BY date").fetchall()
        log = {}
        for row in rows:
            date_str = row["date"]
            period = row["period"]
            if date_str not in log:
                log[date_str] = {}
            log[date_str][period] = {
                "completed_at": row["completed_at"],
                "tasks": json.loads(row["tasks"]) if row["tasks"] else []
            }
        return log

    # ─── Utility Queries ────────────────────────────────────────────────

    def get_campaign_names(self) -> list[str]:
        """Get all campaign names."""
        conn = self._get_conn()
        rows = conn.execute("SELECT name FROM campaigns ORDER BY name").fetchall()
        return [r["name"] for r in rows]

    def get_leads_summary(self) -> dict:
        """Get pipeline summary from leads table."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT status, COUNT(*) as count FROM leads GROUP BY status
        """).fetchall()
        summary = {"total": 0}
        for r in rows:
            summary[r["status"]] = r["count"]
            summary["total"] += r["count"]
        # Ensure all statuses are present
        for s in ["new", "contacted", "meeting_set", "interested",
                   "negotiation", "closed", "lost"]:
            summary.setdefault(s, 0)
        return summary

    def get_content_stats(self) -> dict:
        """Get 80/20 stats from content_ideas table."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) as c FROM content_ideas").fetchone()["c"]
        value = conn.execute(
            "SELECT COUNT(*) as c FROM content_ideas WHERE content_type = 'value'"
        ).fetchone()["c"]
        posted = conn.execute(
            "SELECT COUNT(*) as c FROM content_ideas WHERE posted = 1"
        ).fetchone()["c"]
        scheduled = conn.execute(
            "SELECT COUNT(*) as c FROM content_ideas WHERE scheduled_date != '' AND posted = 0"
        ).fetchone()["c"]
        promo = total - value
        ratio = value / total if total > 0 else 0
        return {
            "total": total,
            "value": value,
            "promotion": promo,
            "ratio": round(ratio, 2),
            "target_ratio": 0.8,
            "compliant": ratio >= 0.8,
            "posted": posted,
            "scheduled": scheduled
        }

    def get_group_pipeline(self) -> dict:
        """Get group pipeline summary."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT status, COUNT(*) as count FROM group_prospects GROUP BY status
        """).fetchall()
        summary = {"total_prospects": 0}
        for r in rows:
            summary[r["status"]] = r["count"]
            summary["total_prospects"] += r["count"]
        for s in ["discovered", "pending_test", "testing", "active", "rejected"]:
            summary.setdefault(s, 0)
        summary["allows_promotion"] = conn.execute(
            "SELECT COUNT(*) as c FROM group_prospects WHERE allows_promotion = 1"
        ).fetchone()["c"]
        summary["high_engagement"] = conn.execute(
            "SELECT COUNT(*) as c FROM group_prospects WHERE engagement_score >= 70"
        ).fetchone()["c"]
        return summary

    def get_leads_by_status(self, status: str) -> list[dict]:
        """Get leads filtered by status."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC", (status,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_leads_needing_followup(self) -> list[dict]:
        """Get leads that need follow-up (not closed/lost)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM leads WHERE status NOT IN ('closed', 'lost') ORDER BY last_contact ASC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_groups_by_status(self, status: str) -> list[dict]:
        """Get group prospects by status."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM group_prospects WHERE status = ? ORDER BY name", (status,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_active_groups(self) -> list[dict]:
        """Get active groups that allow promotion."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM group_prospects WHERE status = 'active' AND allows_promotion = 1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    # ─── Cleanup ────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def __del__(self) -> None:
        """Ensure connection is closed on garbage collection."""
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
