import os
import traceback

import httpx
from openai import OpenAI


def main():
    base_url = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_CHAT_MODEL")
    api_key = os.environ.get("LLM_API_KEY")

    print(f"base_url={base_url}")
    print(f"model={model}")
    print(f"api_key_set={bool(api_key and api_key != 'replace-with-your-api-key')}")

    verify = os.environ.get("LLM_SSL_VERIFY", "true").lower() not in {"0", "false", "no"}
    trust_env = os.environ.get("LLM_TRUST_ENV", "true").lower() not in {"0", "false", "no"}
    print(f"ssl_verify={verify}")
    print(f"trust_env={trust_env}")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.Client(verify=verify, trust_env=trust_env),
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=8,
        )
        print("OK")
        print(response.choices[0].message.content)
    except Exception as exc:
        print(type(exc).__name__)
        print(str(exc))
        print(f"cause={repr(getattr(exc, '__cause__', None))}")
        traceback.print_exc(limit=4)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
