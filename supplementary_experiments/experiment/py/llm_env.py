import os
import time

import httpx
from openai import OpenAI


def env_value(name, default=None, required=False):
    value = os.environ.get(name)
    if value is None or value == "":
        value = default
    if required and (value is None or value == "" or value == "replace-with-your-api-key"):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def env_first(names, default=None, required=False):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    if required and (default is None or default == "" or default == "replace-with-your-api-key"):
        raise RuntimeError(f"Missing required environment variable. Tried: {', '.join(names)}")
    return default


def env_int(name, default):
    value = env_value(name, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def env_float(name, default):
    value = env_value(name, str(default))
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def openai_client(api_key_env, base_url_env, default_base_url):
    api_key_names = api_key_env if isinstance(api_key_env, (list, tuple)) else [api_key_env]
    base_url_names = base_url_env if isinstance(base_url_env, (list, tuple)) else [base_url_env]
    api_key = env_first(api_key_names, required=True)
    base_url = env_first(base_url_names, default_base_url, required=default_base_url is None)
    verify = env_value("LLM_SSL_VERIFY", "true").lower() not in {"0", "false", "no"}
    trust_env = env_value("LLM_TRUST_ENV", "false").lower() not in {"0", "false", "no"}
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.Client(verify=verify, trust_env=trust_env),
    )


def chat_completion_content_with_retry(client, context, **kwargs):
    attempts = max(1, env_int("LLM_API_MAX_RETRIES", 3))
    delay_seconds = max(0.0, env_float("LLM_API_RETRY_DELAY_SECONDS", 2.0))
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            if kwargs.get("stream"):
                response_content = ""
                for chunk in response:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta.content:
                        response_content += delta.content
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        response_content += delta.reasoning_content
                return response_content

            if not response.choices:
                return ""
            message = response.choices[0].message
            return message.content or ""
        except Exception as exc:
            last_error = exc
            print(f"[LLM API] {context} failed on attempt {attempt}/{attempts}: {exc}")
            if attempt >= attempts:
                break
            time.sleep(delay_seconds * attempt)

    raise RuntimeError(f"LLM API failed after {attempts} attempts: {context}") from last_error
