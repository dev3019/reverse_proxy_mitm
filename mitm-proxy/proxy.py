from mitmproxy import http
import json, os
from dataclasses import asdict

from guardian_client import GuardianClient
from decision import DecisionEngine
from logger import log_block, log_error
from rate_limiter import RateLimiter

guardian_client = GuardianClient("http://guardian:8000")

guardian_limiter = RateLimiter(rate=3, per_seconds=60) # open ai free tier limit is 3 requests per minute

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_HOST = "generativelanguage.googleapis.com"
GEMINI_PATH = "/v1beta/models/gemini-3-flash-preview:generateContent"

def _truncate_at_word(text: str, max_len: int = 125) -> str:
    """Return a <= max_len preview, cutting back to the last whole word."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text

    cut = text[:max_len].rstrip()
    # If we cut in the middle of a word, back up to the previous whitespace.
    last_space = cut.rfind(" ")
    return cut[:last_space].rstrip() if last_space > 0 else cut

class MITMGateway:
    async def request(self, flow: http.HTTPFlow):
        if flow.request.method == "POST":
            content_type = flow.request.headers.get("Content-Type", "")
            if 'application/json' not in content_type:
                return
            raw = flow.request.get_text(strict=False) or ""

            try:
                data = json.loads(raw) if raw.strip() else {}
                if 'text' not in data:
                    log_block(flow, "Missing or invalid input field")
                    flow.response = http.Response.make(
                        400,
                        json.dumps({"success": False, "reason": "Missing required field: text"}),
                        {"Content-Type": "application/json"},
                    )
                    return

                prompt = data['text']
                prompt_preview = _truncate_at_word(prompt)
                scores = await guardian_client.get_toxicity_score(prompt)
                decision = DecisionEngine.decide(scores)

                if not decision.allow:
                    log_block(flow, decision.reason, prompt_preview)
                    flow.response = http.Response.make(
                        403,
                        json.dumps({"success": decision.allow, "reason": f'The prompt was blocked because it contained {decision.reason}.'}),
                        {"Content-Type": "application/json"}
                    )
                    return
                
                
                allowed = await guardian_limiter.allow()
                if not allowed:
                    log_block(flow, "Guardian rate limit exceeded", prompt_preview)
                    flow.response = http.Response.make(
                        429,
                        json.dumps({
                            "success": False,
                            "reason": "Rate limit exceeded"
                        }),
                        {"Content-Type": "application/json"},
                    )
                    return
                
                enforced_payload = {
                    "contents": [
                        {"parts": [{"text": prompt}]}
                    ]
                }

                body = json.dumps(enforced_payload).encode('utf-8')
                flow.request.content = body

                flow.request.scheme = "https"
                flow.request.host = GEMINI_HOST
                flow.request.port = 443
                flow.request.path = GEMINI_PATH
                flow.request.http_version = "HTTP/1.1"

                flow.request.headers.clear()
                flow.request.headers.update({
                    "Host": GEMINI_HOST,
                    "x-goog-api-key": f"{GEMINI_API_KEY}",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "Connection": "close",
                })

            except Exception as error:
                log_error(flow, error)
                flow.response = http.Response.make(
                    503,
                    json.dumps({"success": False, "reason": "Service Unavailable"}),
                    {"Content-Type": "application/json"}
                )
                return

    async def response(self, flow: http.HTTPFlow):
        if flow.response.status_code == 200:
            content = flow.response.get_text(strict=False) or ""
            try:
                data = json.loads(content) or {}
                try:
                    extracted_text = data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError, TypeError):
                    raise ValueError("Invalid response from Gemini API: missing candidates[0].content.parts[0].text")

                payload = {"text": extracted_text}
                body = json.dumps(payload).encode("utf-8")

                flow.response.content = body
                flow.response.headers.pop("content-encoding", None)
                flow.response.headers.pop("transfer-encoding", None)
                flow.response.headers["Content-Type"] = "application/json"
                flow.response.headers["Content-Length"] = str(len(body))
                return
            except Exception as error:
                log_error(flow, error)
                flow.response = http.Response.make(
                    503,
                    json.dumps({"success": False, "reason": "Service Unavailable"}),
                    {"Content-Type": "application/json"}
                )
                return
addons = [MITMGateway()]
