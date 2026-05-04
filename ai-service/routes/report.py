from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.cache import get_cache, set_cache
from services.metrics import record_ai_response_time
import json
from datetime import datetime
import time

report_bp = Blueprint("report", __name__)

def build_prompt(threat, recommendations):
    return f"""
Generate a cybersecurity incident report in STRICT JSON.

Threat:
{threat}

Recommendations:
{recommendations}

Rules:
- Return ONLY JSON
- No markdown
- No explanation

Format:
{{
  "title": "string",
  "summary": "string",
  "overview": "string",
  "key_items": ["item1", "item2", "item3"],
  "recommendations": [
    {{
      "action_type": "string",
      "description": "string",
      "priority": "Low | Medium | High"
    }}
  ]
}}
"""

@report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.json

    threat = data.get("threat")
    recommendations = data.get("recommendations")

    if not threat or not recommendations:
        return jsonify({
            "error": "Threat and recommendations required",
            "report": {}
        }), 400

    try:
        prompt = build_prompt(threat, recommendations)
        cached_result = get_cache(prompt)

        if cached_result:
            cached_result["cached"] = True
            cached_result["generated_at"] = datetime.utcnow().isoformat()
            return jsonify(cached_result), 200

        start_time = time.time()
        ai_response = call_groq(prompt)
        record_ai_response_time(time.time() - start_time)

        print("RAW REPORT:", ai_response)

        # Clean markdown
        ai_response = ai_response.strip().replace("```json", "").replace("```", "")

        report = json.loads(ai_response)

        result = {
            "report": report,
            "generated_at": datetime.utcnow().isoformat(),
            "is_fallback": False
        }

        set_cache(prompt, {"report": report, "is_fallback": False})
        return jsonify(result)

    except Exception as e:
        print("REPORT ERROR:", str(e))

        # Fallback (MANDATORY for this task)
        return jsonify({
            "report": {
                "title": "Fallback Report",
                "summary": "AI generation failed",
                "overview": "Manual review required",
                "key_items": ["Check logs", "Investigate issue"],
                "recommendations": recommendations or []
            },
            "generated_at": datetime.utcnow().isoformat(),
            "is_fallback": True
        }), 200