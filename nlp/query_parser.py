import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

_client = None

SYSTEM_PROMPT = """You are a video surveillance query parser for VideoGPT.
Extract search parameters from the user query and return ONLY valid JSON.

JSON keys (omit keys not mentioned in query):
{
  "action": "search" | "investigate",
  "plate": "plate string or null",
  "vehicle_type": "car|truck|bus|motorcycle or null",
  "vehicle_color": "red|white|black|blue|green|yellow|silver|orange or null",
  "cameras": ["gate1","gate2","gate3"] or null,
  "direction": "entering|exiting or null"
}

Examples:
Query: show red cars in gate1 gate2
Output: {"action":"search","vehicle_color":"red","vehicle_type":"car","cameras":["gate1","gate2"]}

Query: investigate car ABC-1234 across gate1 gate3 timeline
Output: {"action":"investigate","plate":"ABC-1234","cameras":["gate1","gate3"]}

Query: show all trucks
Output: {"action":"search","vehicle_type":"truck"}

Return ONLY the JSON object, no extra text."""


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key or api_key == "your_groq_api_key_here":
            return None
        _client = Groq(api_key=api_key)
    return _client


def parse_query(user_query: str) -> dict:
    client = _get_client()
    if client:
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_query}
                ],
                temperature=0.1,
                max_tokens=256
            )
            raw = response.choices[0].message.content.strip()
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                parsed = json.loads(m.group())
                logger.info(f"[NLP] LLM parsed: {parsed}")
                return parsed
        except Exception as e:
            logger.warning(f"[NLP] Groq error: {e}. Using fallback.")

    return _fallback_parser(user_query)


def _fallback_parser(query: str) -> dict:
    q      = query.lower()
    result = {"action": "search"}

    gates = re.findall(r"gate\s*\d+", q)
    gates = [g.replace(" ", "") for g in gates]
    if gates:
        result["cameras"] = list(set(gates))

    plate = re.search(r"[A-Z]{2,4}[-\s]?\d{2,4}", query.upper())
    if plate:
        result["plate"]  = plate.group().replace(" ", "-")
        result["action"] = "investigate"

    for color in ["red", "white", "black", "blue", "green",
                  "yellow", "silver", "orange", "brown"]:
        if color in q:
            result["vehicle_color"] = color
            break

    for vtype in ["car", "truck", "bus", "motorcycle"]:
        if vtype in q:
            result["vehicle_type"] = vtype
            break

    if any(w in q for w in ["investigate", "timeline", "trace", "track"]):
        result["action"] = "investigate"

    logger.info(f"[NLP] Fallback parsed: {result}")
    return result
