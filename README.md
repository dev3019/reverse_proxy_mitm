# Reverse Proxy + MITM + Guardian (Local Content Safety Gate)

This repo runs an HTTPS endpoint (nginx) that forwards requests through a **mitmproxy addon** (`mitm-proxy/proxy.py`).  
The proxy:
- classifies the incoming prompt using a local **Guardian service** (`guardian/app.py`)
- blocks unsafe prompts (403)
- rate-limits upstream LLM calls (429)
- forwards allowed prompts to Gemini and rewrites Gemini’s response to a small JSON payload `{ "text": "..." }`

## How to run (Docker Compose)

### Prerequisites
- Docker Desktop
- A Gemini API key
- TLS certs for nginx (`nginx/certs/server.crt` and `nginx/certs/server.key`)

#### Generate TLS certs (do this BEFORE `docker compose up --build`)
From the **repo root**:

```bash
mkdir -p nginx/certs

openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

### 1) Create `.env`
Create a `.env` file in the repo root:

```bash
GEMINI_API_KEY=your_key_here
```

`docker-compose.yml` mounts this into the `mitmproxy` service via `env_file`.

### 2) Start the stack

```bash
docker compose up --build
```

### 3) Send a test request
From `client/`:

```bash
python3 send_request.py
```

## Rate limiting (and production note)

- **Current limit**: **3 requests/minute** at `mitm-proxy/proxy.py` (chosen because Gemini free tier is very limited; we keep it conservative).
- **Production**: use **Redis-backed rate limiting** (shared state across replicas + survives restarts). The current in-memory limiter resets on container restart and only applies per-container.

## Guardian model choice on macOS (why not vLLM + Granite Guardian)

We initially aimed for **vLLM + Granite Guardian**, but on **macOS + Docker Desktop** it’s not practical (no NVIDIA GPU passthrough + heavy runtime/storage requirements).

Instead, `guardian/app.py` runs a lightweight CPU-friendly setup:
- `unitary/toxic-bert` for **overall toxicity** (line 10)
- `typeform/distilbert-base-uncased-mnli` for **zero-shot** classification of:
  - violence
  - sexual content
  - illegal activity (line 11)

## Testing different scenarios

Use `client/concurrent_requests.py` to spam different prompts and validate:
- violence / toxic / illegal / sexual → **403**
- safe prompt but rate limit exceeded → **429**
- guardian service down / proxy exception / upstream issues → **503**
- safe + within limits → **200**

From `client/`:

```bash
python3 concurrent_requests.py
```

## Status codes (what they mean)

- **200**: request allowed; response normalized to `{ "text": "..." }`
- **403**: blocked by Guardian policy (prompt unsafe)
- **429**: rate limit exceeded before calling Gemini
- **503**: proxy-side failure (guardian unreachable, parse error, unexpected exception, etc.)