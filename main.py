def ask_ai(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "کلیلی AI ڕێکنەخراوە."
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser: {prompt}"}]
            }]
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.HTTPError as e:
        # لێرەدا دەهێڵین تەنها جۆری هەڵەکە نیشان بدات بە بێ نیشاندانی لینکی API
        status_code = e.response.status_code if e.response else "نادیار"
        return f"هەڵەی پەیوەندی بە جیمینای (کۆد: {status_code})."
    except Exception as e:
        return f"هەڵەیەک ڕوویدا لە وەرگرتنی وەڵام."
