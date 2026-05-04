from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.cache import get_cache, set_cache
from services.metrics import record_ai_response_time
import json
from datetime import datetime
import time

recommend_bp = Blueprint("recommend", __name__)

def load_prompt(user_input):
    with open("prompts/recommend.txt", "r", encoding="utf-8") as f:
        return f.read().replace("{input}", user_input)

@recommend_bp.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True)

    if not data or "input" not in data:
        return jsonify({
            "error": "Missing required field: input",
            "recommendations": []
        }), 400

    user_input = data["input"]

    if len(user_input) < 3:
        return jsonify({
            "error": "Input is too short (min 3 chars)",
            "recommendations": []
        }), 400

    if len(user_input) > 2000:
        return jsonify({
            "error": "Input is too long (max 2000 chars)",
            "recommendations": []
        }), 400

    try:
        prompt = load_prompt(user_input)
        cached_result = get_cache(prompt)

        if cached_result:
            cached_result["cached"] = True
            cached_result["generated_at"] = datetime.utcnow().isoformat()
            return jsonify(cached_result), 200

        start_time = time.time()
        ai_response = call_groq(prompt)
        record_ai_response_time(time.time() - start_time)

        if ai_response:
            ai_response = ai_response.strip()
            ai_response = ai_response.replace("```json", "").replace("```", "").strip()

        recommendations = json.loads(ai_response)

        if not isinstance(recommendations, list):
            raise ValueError("Invalid AI response format")

        result = {
            "recommendations": recommendations[:3],
            "generated_at": datetime.utcnow().isoformat(),
            "is_fallback": False
        }

        set_cache(prompt, {"recommendations": recommendations[:3], "is_fallback": False})
        return jsonify(result), 200

    except Exception as e:
        print("AI ERROR:", str(e))

        return jsonify({
            "recommendations": [
                {
                    "action_type": "monitor",
                    "description": "Fallback: Monitor system logs",
                    "priority": "high"
                },
                {
                    "action_type": "alert",
                    "description": "Fallback: Notify admin",
                    "priority": "medium"
                },
                {
                    "action_type": "patch",
                    "description": "Fallback: Apply updates",
                    "priority": "low"
                }
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "is_fallback": True
        }), 200