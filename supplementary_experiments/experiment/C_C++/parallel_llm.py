import os


def get_llm_workers(default=4):
    raw_value = os.getenv("LLM_PARALLEL_WORKERS", str(default)).strip()
    try:
        workers = int(raw_value)
    except ValueError:
        workers = default
    return max(1, workers)
