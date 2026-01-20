from mitmproxy import http
import json
from dataclasses import asdict

from guardian_client import GuardianClient
from decision import DecisionEngine
from logger import log_block, log_error
from rate_limiter import RateLimiter

guardian_client = GuardianClient("http://guardian:8000")

guardian_limiter = RateLimiter(rate=3, per_seconds=60) # open ai free tier limit is 3 requests per minute

class MITMGateway:
    async def request(self, flow: http.HTTPFlow):
        if flow.request.method == "POST":
            content_type = flow.request.headers.get("Content-Type", "")
            if 'application/json' not in content_type:
                return
            raw = flow.request.get_text(strict=False) or ""

            try:
                data = json.loads(raw) if raw.strip() else {}
                if 'text' in data:
                    
                    # allowed = await guardian_limiter.allow()
                    # if not allowed:
                    #     log_block(flow, "Guardian rate limit exceeded", data['text'])
                    #     flow.response = http.Response.make(
                    #         429,
                    #         json.dumps({
                    #             "success": False,
                    #             "reason": "Rate limit exceeded"
                    #         }),
                    #         {"Content-Type": "application/json"},
                    #     )
                    #     return
                    
                    scores = await guardian_client.get_toxicity_score(data['text'])
                    data['scores'] = asdict(scores)
                    decision = DecisionEngine.decide(scores)

                    if not decision.allow:
                        log_block(flow, decision.reason, data['text'])
                        flow.response = http.Response.make(
                            403,
                            json.dumps({"success": decision.allow, "reason": f'The prompt was blocked because it contained {decision.reason}.'}),
                            {"Content-Type": "application/json"}
                        )
                        return
                    
                    
                    allowed = await guardian_limiter.allow()
                    if not allowed:
                        log_block(flow, "Guardian rate limit exceeded", data['text'])
                        flow.response = http.Response.make(
                            429,
                            json.dumps({
                                "success": False,
                                "reason": "Rate limit exceeded"
                            }),
                            {"Content-Type": "application/json"},
                        )
                        return

                body_bytes = json.dumps(data).encode('utf-8')
                flow.request.content = body_bytes

                flow.request.headers.pop("transfer-encoding", None)
                flow.request.headers["content-type"] = "application/json"
                flow.request.headers['content-length'] = str(len(body_bytes))

            except Exception as error:
                log_error(flow, error)
                flow.response = http.Response.make(
                    503,
                    json.dumps({"success": False, "reason": "Service Unavailable"}),
                    {"Content-Type": "application/json"}
                )
                return

        print("Scheme:", flow.request.scheme)
        print("Host:", flow.request.host)

addons = [MITMGateway()]
