import httpx
import asyncio

from dataclasses import dataclass

@dataclass
class GuardianScores:
    toxicity: float
    sexual: float
    violence: float
    illegal: float

class GuardianClient:
    def __init__(self, base_url: str, timeout: int = 10, max_retries: int = 3, base_backoff: float = 0.5) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_backoff = base_backoff

    async def get_toxicity_score(self, text: str) -> GuardianScores:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries+1):
                try:
                    resp = await client.post(
                        f"{self.base_url}/analyze",
                        json={"text": text}
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    return GuardianScores(
                        toxicity=data.get("toxicity", 0.0),
                        sexual=data.get("sexual", 0.0),
                        violence=data.get("violence", 0.0),
                        illegal=data.get("illegal", 0.0),
                    )
                except Exception:
                    if attempt == self.max_retries:
                        raise

                    backoff = self.base_backoff * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)