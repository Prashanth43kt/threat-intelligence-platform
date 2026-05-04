from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.cache import get_cache, set_cache
from services.metrics import record_ai_response_time
from datetime import datetime, timezone
import json
import time

describe_bp = Blueprint("describe", __name__)

def load_prompt(input_text):
    with open("prompts/describe.txt", "r", encoding="utf-8") as f:
        return f.read().replace("{input}", input_text)

@describe_bp.route("/describe", methods=["POST"])
def describe():
    body = request.get_json(silent=True)

    if not body or "input" not in body:
        return jsonify({"error": "Missing required field: input"}), 400

    user_input = str(body["input"]).strip()

    if len(user_input) < 3:
        return jsonify({"error": "Input is too short"}), 400

    if len(user_input) > 2000:
        return jsonify({"error": "Input is too long (max 2000 chars)"}), 400

    prompt = load_prompt(user_input)
    cached_result = get_cache(prompt)

    if cached_result:
        cached_result["cached"] = True
        cached_result["generated_at"] = datetime.now(timezone.utc).isoformat()
        return jsonify(cached_result), 200

    start_time = time.time()
    ai_response = call_groq(prompt)
    record_ai_response_time(time.time() - start_time)

    # Try parsing AI response as JSON
    try:
        parsed = json.loads(ai_response)
    except Exception:
        return jsonify({
            "error": "AI returned invalid JSON",
            "raw_response": ai_response,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }), 500

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data": parsed
    }

    set_cache(prompt, {"data": parsed})
    return jsonify(result), 200