"""
affiliate-ai-agent/dashboard/api.py
Flask API server that exposes strategy data to the web dashboard.
"""

import os
import sys
from datetime import datetime
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from agent.strategy import StrategyEngine, ContentItem, Lead, Group
from agent.knowledge_base import KnowledgeBase
from agent.group_finder import GroupFinder
from agent.content_planner import ContentPlanner
from agent.lead_tracker import LeadTracker
from agent.campaign import CampaignManager
from automation.facebook_poster import FacebookPoster

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

data_dir = os.path.join(os.path.expanduser("~"), ".affiliate_agent")
engine = StrategyEngine(data_dir)
group_finder = GroupFinder(data_dir)
content_planner = ContentPlanner(data_dir)
lead_tracker = LeadTracker(data_dir)
campaign_manager = CampaignManager(data_dir)
facebook_poster = FacebookPoster(data_dir)


# ─── Static Files ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


# ─── API Routes ──────────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    """API health check."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "configured": engine.is_configured(),
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    """Get or update configuration."""
    if request.method == "POST":
        data = request.json
        engine.update_config(**data)
        return jsonify({"status": "ok", "config": engine.config.to_dict()})
    return jsonify(engine.config.to_dict())


@app.route("/api/pillars")
def api_pillars():
    """Get strategy pillars."""
    return jsonify(engine.PILLARS)


@app.route("/api/pillars/<int:pillar_id>")
def api_pillar_detail(pillar_id: int):
    """Get detailed guidance for a pillar."""
    guidance = engine.get_pillar_guidance(pillar_id)
    if not guidance:
        return jsonify({"error": "Pillar not found"}), 404
    return jsonify(guidance)


# ─── Campaigns ───────────────────────────────────────────────────────────────

@app.route("/api/campaigns", methods=["GET"])
def api_campaigns():
    """List all campaigns."""
    return jsonify([c.to_dict() for c in engine.campaigns])


@app.route("/api/campaigns", methods=["POST"])
def api_create_campaign():
    """Create a new campaign."""
    data = request.json
    camp = engine.create_campaign(
        name=data.get("name", "New Campaign"),
        product=data.get("product", ""),
        product_url=data.get("product_url", ""),
        niche=data.get("niche", engine.config.niche),
        target_sales=int(data.get("target_sales", 10))
    )
    campaign_manager.create(
        name=camp.name, product=camp.product, niche=camp.niche,
        sales_target=camp.target_sales
    )
    return jsonify(camp.to_dict()), 201


@app.route("/api/campaigns/<name>", methods=["GET"])
def api_campaign(name: str):
    """Get campaign details."""
    camp = engine.get_campaign(name)
    if not camp:
        return jsonify({"error": "Campaign not found"}), 404
    return jsonify(camp.to_dict())


@app.route("/api/campaigns/<name>/report")
def api_campaign_report(name: str):
    """Get full campaign report."""
    report = engine.export_campaign_report(name)
    if "error" in report:
        return jsonify(report), 404
    return jsonify(report)


@app.route("/api/campaigns/<name>", methods=["DELETE"])
def api_delete_campaign(name: str):
    """Delete a campaign."""
    if engine.delete_campaign(name):
        campaign_manager.delete(name)
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Not found"}), 404


# ─── Groups ──────────────────────────────────────────────────────────────────

@app.route("/api/groups", methods=["GET"])
def api_groups():
    """List all group prospects."""
    return jsonify([g.to_dict() for g in group_finder.prospects])


@app.route("/api/groups", methods=["POST"])
def api_add_group():
    """Add a group prospect."""
    data = request.json
    prospect = group_finder.add_prospect(
        name=data.get("name", ""),
        url=data.get("url", ""),
        niche=data.get("niche", engine.config.niche),
        member_count=int(data.get("member_count", 0))
    )
    return jsonify(prospect.to_dict()), 201


@app.route("/api/groups/<name>", methods=["PATCH"])
def api_update_group(name: str):
    """Update a group's status, engagement score, and notes."""
    data = request.json
    kwargs = {}
    if "status" in data:
        kwargs["status"] = data["status"]
    if "engagement_score" in data:
        kwargs["engagement_score"] = int(data["engagement_score"])
    if "allows_promotion" in data:
        kwargs["allows_promotion"] = data["allows_promotion"]
    if "notes" in data:
        kwargs["notes"] = data["notes"]
    success = group_finder.update_status(name, **kwargs)
    return jsonify({"success": success})


@app.route("/api/groups/pipeline")
def api_groups_pipeline():
    """Get group pipeline summary."""
    return jsonify(group_finder.get_pipeline_summary())


@app.route("/api/groups/keywords/<niche>")
def api_groups_keywords(niche: str):
    """Get search keywords for a niche."""
    return jsonify({"keywords": group_finder.get_search_keywords(niche)})


# ─── Content ─────────────────────────────────────────────────────────────────

@app.route("/api/content/ideas", methods=["GET"])
def api_content_ideas():
    """List all content ideas."""
    return jsonify([i.to_dict() for i in content_planner.ideas])


@app.route("/api/content/ideas", methods=["POST"])
def api_generate_ideas():
    """Generate new content ideas."""
    data = request.json
    niche = data.get("niche", engine.config.niche)
    count = int(data.get("count", 10))
    ideas = content_planner.generate_ideas(niche, count)
    return jsonify([i.to_dict() for i in ideas]), 201


@app.route("/api/content/stats")
def api_content_stats():
    """Get content 80/20 statistics."""
    return jsonify(content_planner.get_stats())


@app.route("/api/content/calendar")
def api_content_calendar():
    """Get weekly calendar."""
    return jsonify(content_planner.get_weekly_calendar())


@app.route("/api/content/mark-posted", methods=["POST"])
def api_mark_posted():
    """Mark content as posted."""
    data = request.json
    success = content_planner.mark_posted(
        data.get("title", ""),
        data.get("engagement", "")
    )
    return jsonify({"success": success})


# ─── Leads ───────────────────────────────────────────────────────────────────

@app.route("/api/leads", methods=["GET"])
def api_leads():
    """List all leads."""
    return jsonify([l.to_dict() for l in lead_tracker.leads])


@app.route("/api/leads", methods=["POST"])
def api_add_lead():
    """Register a new lead."""
    data = request.json
    lead = lead_tracker.add_lead(
        name=data.get("name", ""),
        phone=data.get("phone", ""),
        source_group=data.get("source_group", ""),
        product_interest=data.get("product_interest", "")
    )
    return jsonify(lead.to_dict()), 201


@app.route("/api/leads/pipeline")
def api_leads_pipeline():
    """Get lead pipeline summary."""
    return jsonify(lead_tracker.get_pipeline_summary())


@app.route("/api/leads/weekly-report")
def api_leads_weekly():
    """Get weekly lead report."""
    return jsonify(lead_tracker.get_weekly_report())


@app.route("/api/leads/followup")
def api_leads_followup():
    """Get leads needing follow-up."""
    needing = lead_tracker.get_leads_needing_followup()
    return jsonify([
        {"lead": l.to_dict(), "step": s}
        for l, s in needing
    ])


@app.route("/api/leads/<phone>", methods=["PATCH"])
def api_update_lead(phone: str):
    """Update a lead's status."""
    data = request.json
    notes = data.get("notes", "")
    success = lead_tracker.update_status(phone, data["status"], notes)
    return jsonify({"success": success})


@app.route("/api/waling-link")
def api_waling_link():
    """Generate wa.link URL."""
    phone = request.args.get("phone", engine.config.whatsapp_number)
    return jsonify({
        "link": lead_tracker.generate_waling_link(phone) if phone else ""
    })


# ─── Knowledge Base ──────────────────────────────────────────────────────────

@app.route("/api/knowledge/sales-psychology")
def api_sales_psychology():
    return jsonify({"tips": KnowledgeBase.SALES_PSYCHOLOGY_TIPS})


@app.route("/api/knowledge/value-content")
def api_value_content():
    return jsonify({"types": KnowledgeBase.VALUE_CONTENT_TYPES})


@app.route("/api/knowledge/niches")
def api_niches():
    return jsonify({"niches": KnowledgeBase.PROFITABLE_NICHES})


@app.route("/api/knowledge/whatsapp-script")
def api_whatsapp_script():
    return jsonify(KnowledgeBase.WHATSAPP_SCRIPT)


@app.route("/api/knowledge/metrics")
def api_metrics():
    return jsonify({"metrics": KnowledgeBase.KEY_METRICS})


# ─── Dashboard Summary ───────────────────────────────────────────────────────

# ─── Facebook Poster API ───────────────────────────────────────────────

@app.route("/api/facebook/status")
def api_facebook_status():
    """Get Facebook Poster session status."""
    status = facebook_poster.get_session_status()
    stats = facebook_poster.get_stats()
    return jsonify({
        "status": status,
        "stats": stats,
        "config": facebook_poster.config.to_dict(),
    })


@app.route("/api/facebook/config", methods=["POST"])
def api_facebook_config():
    """Update Facebook Poster configuration."""
    data = request.json
    for k, v in data.items():
        if hasattr(facebook_poster.config, k):
            setattr(facebook_poster.config, k, v)
    facebook_poster._save_config()
    return jsonify({"success": True, "config": facebook_poster.config.to_dict()})


@app.route("/api/facebook/post", methods=["POST"])
def api_facebook_post():
    """Execute automatic posting to active Facebook groups."""
    data = request.json or {}
    max_posts = int(data.get("max_posts", 5))
    content = data.get("content", None)

    if not facebook_poster.config.enabled:
        return jsonify({
            "success": False,
            "error": "Facebook Poster no está habilitado"
        }), 400

    status = facebook_poster.get_session_status()
    if not status["profile_exists"]:
        return jsonify({
            "success": False,
            "error": "Perfil de Chrome no configurado. Usa: python run.py --fb-setup"
        }), 400

    # Ejecutar en segundo plano (simplificado - ejecución síncrona)
    try:
        results = facebook_poster.post_to_active_groups(
            content_override=content,
            max_posts=max_posts
        )
        success_count = sum(1 for r in results if r.success)
        return jsonify({
            "success": True,
            "results": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/facebook/stats")
def api_facebook_stats():
    """Get Facebook Poster statistics."""
    return jsonify(facebook_poster.get_stats())


@app.route("/api/facebook/post-log")
def api_facebook_post_log():
    """Get recent post log using public method."""
    posts = facebook_poster.get_recent_posts(20)
    return jsonify({
        "posts": posts,
        "total": len(posts)
    })


# ─── Dashboard Summary ───────────────────────────────────────────────────────

@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    """Get a complete dashboard summary."""
    fb_status = facebook_poster.get_session_status()
    fb_stats = facebook_poster.get_stats()
    return jsonify({
        "campaigns": [c.to_dict() for c in engine.campaigns],
        "groups": group_finder.get_pipeline_summary(),
        "content": content_planner.get_stats(),
        "leads": lead_tracker.get_pipeline_summary(),
        "config": engine.config.to_dict(),
        "active_campaigns_count": len(engine.campaigns),
        "total_groups": len(group_finder.prospects),
        "total_leads": len(lead_tracker.leads),
        "total_content": len(content_planner.ideas),
        "facebook": {
            "configured": fb_status["configured"],
            "profile_exists": fb_status["profile_exists"],
            "cookies_exist": fb_status["cookies_exist"],
            "posts_today": fb_status["posts_today"],
            "remaining_today": fb_status["remaining_today"],
            "total_posts_logged": fb_status["total_posts_logged"],
            "total_success": fb_stats["total_success"],
            "total_failures": fb_stats["total_failures"],
        }
    })


def start_dashboard(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start the dashboard web server."""
    print(f"🌐 Dashboard web iniciado en http://localhost:{port}")
    print(f"📊 API disponible en http://localhost:{port}/api/")
    print("Presiona Ctrl+C para detener el servidor")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_dashboard(debug=True)
