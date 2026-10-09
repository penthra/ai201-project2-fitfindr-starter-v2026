"""Exercise the real MCP/model path with an intentionally invalid API key.

Run `python run_failure_check.py`. The saved .env and real key are unchanged.
Only the MCP subprocesses created during this check receive the invalid key.
"""

import json
from unittest.mock import patch

import config
import mcp
import trace
from agent import run_agent
from utils.data_loader import get_example_wardrobe


def main():
    config.CACHE_ENABLED = False
    original_parameters = mcp.StdioServerParameters

    def invalid_key_parameters(**kwargs):
        kwargs["env"] = {
            **(kwargs.get("env") or {}),
            "GEMINI_API_KEY": "intentionally-invalid-unit4-test-key",
            "AI201_CACHE": "0",
        }
        return original_parameters(**kwargs)

    trace.start_trace()
    print("Failure check: real MCP calls with an intentionally invalid API key.")
    print("The saved .env and real key are unchanged; caching is disabled.")
    with patch.object(mcp, "StdioServerParameters", invalid_key_parameters):
        try:
            session = run_agent(
                "vintage graphic tee under $30", get_example_wardrobe()
            )
        except Exception as exc:
            print(f"UNHANDLED: {type(exc).__name__}: {exc}")
            return 1

    print("Returned session:")
    print(json.dumps(session, ensure_ascii=False, indent=2))
    if session.get("error"):
        print("HANDLED: the agent returned an error message instead of raising.")
        return 0
    print("NOT TRIGGERED: no model failure was reported.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
