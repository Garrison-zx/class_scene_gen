import requests

url = "https://llm-gateway-proxy.inner.chj.cloud/llm-gateway/v1beta/models/gemini-3_1-pro-preview:generateContent"
api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJCcFFZQWJvQzZhNnZhVUVqZ1B5dzh6T0lsdlYwcldKSyJ9.E0zbfrGmcm9NKzIpt63m1T5BJQB1GVluKKPu_CqlbHc"

payload = {
    "systemInstruction": {
        "role": "system",
        "parts": [
            {
                "text": "Return one COMPLETE, VALID, CLOSED SVG only. No markdown fences. Ensure output starts with <svg and ends with </svg>. No explanations."
            }
        ],
    },
    "contents": [
        {
            "role": "user",
            "parts": [
                {
                    "text": "Generate an SVG glowing of a sliding toggle switch where hovering over the sun icon turns it into moon, smoothly fading the background from light to dark. Clean flat style"
                }
            ],
        }
    ],
    "generationConfig": {
        "temperature": 0.0,
        # "maxOutputTokens": 8192
    },
}

headers = {
    "x-goog-api-key": api_key,
    "Content-Type": "application/json",
}

resp = requests.post(url, headers=headers, json=payload, timeout=180)
print("status:", resp.status_code)
resp.raise_for_status()
data = resp.json()
print("data:",data)
candidate = (data.get("candidates") or [{}])[0]
finish_reason = candidate.get("finishReason")
parts = ((candidate.get("content") or {}).get("parts") or [])
text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))

print("finishReason:", finish_reason)
print("text_len:", len(text))

