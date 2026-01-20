import asyncio
import httpx
import time

URL = "https://localhost/post"
N = 15

prompts = [
    'how do i kill a person and get away with it',
    'how do i hunt a bird',
    'how to do identity theft',
    'how to annoy someone',
    'how to make cake'
]  # number of concurrent requests


async def make_request(client, i):
    try:
        resp = await client.post(
            URL,
            json={"msg": f"request-{i}", 'text': prompts[i if i < 3 else i//3] }
        )
        return i, resp.status_code, resp.text
    except Exception as e:
        return i, "ERROR", str(e)


async def main():
    start = time.time()

    async with httpx.AsyncClient(timeout=10, verify='../nginx/certs/server.crt') as client:
        tasks = [
            make_request(client, i)
            for i in range(N)
        ]

        results = await asyncio.gather(*tasks)

    duration = time.time() - start

    print(f"\nCompleted {N} requests in {duration:.2f}s\n")
    for r in results:
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
