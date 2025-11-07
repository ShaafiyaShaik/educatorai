"""End-to-end test for the Simple Gemini Chatbot endpoint.

This script will:
 - wait for the local dev server to expose OpenAPI (/openapi.json)
 - POST a sample message to the /api/v1/simple-chatbot/message endpoint
 - call the agent directly (bypassing HTTP/auth) to inspect the parsed action

Run: python e2e_test_simple_chatbot.py
"""
import time
import requests
import sys

BASE = "http://127.0.0.1:8003"

def wait_for_openapi(timeout=30):
    for i in range(timeout):
        try:
            r = requests.get(f"{BASE}/openapi.json", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def call_endpoint(payload):
    url = f"{BASE}/api/v1/simple-chatbot/message"
    try:
        r = requests.post(url, json=payload, timeout=30)
        print("HTTP status:", r.status_code)
        print("HTTP response:\n", r.text)
    except Exception as e:
        print("HTTP request failed:", e)


def call_agent_direct(payload):
    try:
        # Import the agent directly from the package
        from app.agents.simple_gemini_chatbot import simple_chatbot

        res = simple_chatbot.chat(message=payload["message"], history=payload.get("history"), language=payload.get("language", "auto"), auto_execute=False)
        print("Agent direct result:\n", res)
    except Exception as e:
        print("Agent direct call failed:", e)


def main():
    print("Waiting for server to be ready at", BASE)
    ok = wait_for_openapi(30)
    if not ok:
        print("Server did not become ready within timeout. Aborting.")
        sys.exit(2)

    payload = {
        "message": "Send message to Jennifer: Please come to my office tomorrow at 10am.",
        "history": [],
        "language": "te",
        "auto_execute": True
    }

    print("\n==> Calling HTTP endpoint (may fail if auth is required)")
    call_endpoint(payload)

    print("\n==> Calling agent directly (bypasses HTTP auth)")
    call_agent_direct(payload)


if __name__ == '__main__':
    main()
