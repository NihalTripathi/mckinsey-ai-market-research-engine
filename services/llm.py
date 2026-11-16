import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv(override=True)


class GeminiUnreachable(RuntimeError):
    """The Gemini service cannot be reached at all (a network problem, not a model problem)."""


def _is_network_error(e) -> bool:
    try:
        import httpx
        return isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout))
    except Exception:
        return False


def _make_client():
    """A client that gives up on a request after 90 seconds, so one stuck call cannot stall a whole run."""
    key = os.getenv("GEMINI_API_KEY")
    try:
        return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=90_000))
    except Exception:
        return genai.Client(api_key=key)


client = _make_client()

MODELS = [
    os.getenv("GEMINI_MODEL"),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
]
MODELS = [m for i, m in enumerate(MODELS) if m and m not in MODELS[:i]]


def ask_json(prompt, schema=None, attempts_per_model=2, temperature=None):
    """Ask Gemini for JSON. Retries when a model is busy or a request times out, and falls back
    to the next model. With a Pydantic schema, returns a validated object of that schema;
    without one, returns a plain dict. A low temperature (0) makes answers more repeatable."""
    settings = {"response_mime_type": "application/json"}
    if schema:
        settings["response_schema"] = schema
    if temperature is not None:
        settings["temperature"] = temperature
    config = types.GenerateContentConfig(**settings)

    last_error = None
    network_failures = 0
    for model in MODELS:
        for attempt in range(attempts_per_model):
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                if schema:
                    return schema.model_validate_json(response.text)
                return json.loads(response.text)
            except errors.ServerError as e:      # model busy: wait, then retry
                last_error = e
                time.sleep(2 * (attempt + 1))
            except errors.ClientError as e:      # e.g. model not found: next model
                last_error = e
                break
            except ValueError as e:              # bad JSON or schema mismatch: retry
                last_error = e
            except Exception as e:               # timeouts and network errors
                last_error = e
                if _is_network_error(e):         # no connection: other models will fail the same way
                    network_failures += 1
                    if network_failures >= 2:
                        raise GeminiUnreachable(
                            "Cannot reach the Gemini service. Check the internet connection, VPN or proxy, "
                            "and firewall, then try again.") from e
                    time.sleep(1)
                else:
                    time.sleep(2 * (attempt + 1))

    raise last_error


def check_gemini():
    """(ok, message): a quick test that Gemini can be reached with the current key and model."""
    try:
        ask_json('Return JSON: {"ok": true}', attempts_per_model=1)
        return True, "Gemini is reachable."
    except GeminiUnreachable as e:
        return False, str(e)
    except errors.ClientError as e:
        return False, f"Gemini rejected the request ({getattr(e, 'code', '')}). Check GEMINI_API_KEY and GEMINI_MODEL in .env."
    except Exception as e:
        return False, f"Gemini check failed: {type(e).__name__}."