from enum import STRICT
from mitmproxy import http, proxy
import json
import time

class MITMGateway:
    def request(self, flow: http.HTTPFlow):
        content_type = flow.request.headers.get("Content-Type", "")
        if 'application/json' not in content_type:
            return
        raw = flow.request.get_text(strict=False) or ""
        try:
            data = json.loads(raw) if raw.strip() else {}
            data['mitm-req'] = True

            body_bytes = json.dumps(data).encode('utf-8')
            flow.request.content = body_bytes

            flow.request.headers.pop("transfer-encoding", None)
            flow.request.headers["content-type"] = "application/json"
            flow.request.headers['content-length'] = str(len(body_bytes))
        except json.JSONDecodeError:
            return

        log = {
            "event": "request",
            "id": flow.id,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text(),
            "timestamp": time.time(),
        }
        print(json.dumps(log, indent=2))
        print("Scheme:", flow.request.scheme)
        print("Host:", flow.request.host)

    def response(self, flow: http.HTTPFlow):
        log = {
            "event": "response",
            "id": flow.id,
            "status_code": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body": flow.response.get_text(),
            "timestamp": time.time(),
        }
        print(json.dumps(log, indent=2))
        print("Scheme:", flow.request.scheme)
        print("Host:", flow.request.host)

addons = [MITMGateway()]
