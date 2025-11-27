import requests
import time
import os

# You can set DEV_TOKEN in the environment to override the hardcoded token.
_FALLBACK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b3VAZXhhbXBsZS5jb20iLCJleHAiOjE3NjMyNzc1ODh9.ca29E148xOx6Lr7ec30d0emiRcpxkC_5VSyoq-kRH7U"
TOKEN = os.getenv("DEV_TOKEN", _FALLBACK)
BASE = "http://127.0.0.1:8003/api/v1/simple-chatbot/message"


def send(message, history=None):
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {"message": message}
    if history:
        payload["history"] = history
    r = requests.post(BASE, headers=headers, json=payload, timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def main():
    history = []
    sequence = [
        "what is my schedule this week?",
        "hi",
        "iam just saying hi",
        "okay so are there any nicole in my class?",
        "what about nichole?",
        "Nichole Smith",
        "okay send a message to that student to meet me in my office tomorrow to discuss about their attandance",
        # Test misspellings / phonetic variants
        "Message Nichole Smit to meet me tomorrow at 10",
        "Message Niccol Smyth to meet me tomorrow at 10",
        "Message Nicole Smythe to meet me tomorrow at 10"
    ]

    for msg in sequence:
        status, resp = send(msg, history=history)
        print("\n> ", msg)
        print(status)
        print(resp)
        # Append assistant reply into history in the expected shape
        # The API returns {'reply':..., 'action':..., 'executed':...}
        if isinstance(resp, dict):
            assistant_text = resp.get('reply') or ''
        else:
            assistant_text = str(resp)
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": assistant_text})
        time.sleep(0.4)


if __name__ == '__main__':
    main()
