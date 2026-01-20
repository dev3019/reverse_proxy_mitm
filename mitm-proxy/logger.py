def log_block(flow, reason: str, prompt: str):
    print(
        "[BLOCK]",
        {
            "client": flow.client_conn.address,
            "path": flow.request.path,
            "reason": reason,
            "data": prompt,
        }
    )


def log_error(flow, error: Exception):
    print(
        "[ERROR]",
        {
            "client": flow.client_conn.address,
            "path": flow.request.path,
            "error": str(error),
        }
    )
