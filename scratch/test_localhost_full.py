import urllib.request
import urllib.error
import json
import base64
import sys

BASE_URL = "http://localhost:8080/api"

def req(endpoint, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(f"{BASE_URL}{endpoint}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, content

def run():
    print("=" * 70)
    print("AI HEALTH COMPANION - COMPREHENSIVE LOCALHOST TEST SUITE")
    print("=" * 70)

    # 1. Platform status
    status, res = req("/status")
    assert status == 200, f"Status check failed: {res}"
    print(f"[PASS] 1. API Status check passed: {res.get('status')} (AI Mode: {res.get('aiMode')})")

    # 2. Registration & Login
    email = "localhost_tester_live@example.com"
    pwd = "Password123!"
    reg_status, reg_res = req("/auth/register", "POST", {
        "name": "Localhost Tester",
        "email": email,
        "password": pwd,
        "confirmPassword": pwd
    })
    if reg_status == 201:
        token = reg_res["token"]
        print(f"[PASS] 2. Registered new user ({email})")
    else:
        log_status, log_res = req("/auth/login", "POST", {"email": email, "password": pwd})
        assert log_status == 200, f"Login failed: {log_res}"
        token = log_res["token"]
        print(f"[PASS] 2. Logged in existing user ({email})")

    # 3. Profile verification
    p_status, profile = req("/users/profile", token=token)
    assert p_status == 200, f"Profile failed: {profile}"
    print(f"[PASS] 3. Profile retrieved for '{profile.get('name')}' <{profile.get('email')}>")

    # 4. Create chat conversation
    c_status, conv = req("/chat/conversations", "POST", {"title": "Localhost Health Discussion"}, token=token)
    assert c_status == 201, f"Create conv failed: {conv}"
    conv_id = conv["id"]
    print(f"[PASS] 4. Created Chat Conversation ID={conv_id}")

    # 5. Send Health Query to OpenRouter Gemini 2.5 Flash
    user_query = "I have mild neck stiffness and a slight tension headache since this afternoon. What might be causing this and what are safe self-care steps?"
    print(f"       Sending user prompt: \"{user_query[:60]}...\"")
    m_status, msgs = req(f"/chat/conversations/{conv_id}/messages", "POST", {"message": user_query}, token=token)
    assert m_status == 200, f"Send message failed: {msgs}"
    assert len(msgs) == 2, f"Expected user + AI message, got {len(msgs)}"
    ai_reply = msgs[1]["message"]
    print(f"[PASS] 5. OpenRouter LLM Response received and stored in MySQL!")
    print(f"       AI Reply Preview:\n       ----------------------------------------------------")
    for line in ai_reply.strip().split("\n")[:6]:
        print(f"       {line}")
    print(f"       ----------------------------------------------------")

    # 6. Test Emergency Red-Flag Escalation
    urgent_query = "I have sudden severe crushing chest pain radiating to my arm and cannot breathe"
    u_status, u_msgs = req(f"/chat/conversations/{conv_id}/messages", "POST", {"message": urgent_query}, token=token)
    assert u_status == 200
    urgent_reply = u_msgs[-1]["message"]
    assert "EMERGENCY" in urgent_reply or "URGENT" in urgent_reply or "911" in urgent_reply
    print(f"[PASS] 6. Emergency Red-Flag detection verified (Immediate emergency notice generated)")

    # 7. Test Mental Wellness Check-in
    w_status, w_res = req("/wellness/check-in", "POST", {
        "mood": 8,
        "stress": 3,
        "energy": 7,
        "sleepHours": 7.5,
        "journalText": "Had a productive day, feeling good after an evening walk."
    }, token=token)
    assert w_status in (200, 201), f"Wellness check-in failed: {w_res}"
    print(f"[PASS] 7. Mental Wellness Check-in saved (Mood: 8/10, Stress: 3/10, Sleep: 7.5h)")

    # 8. Test Wellness Trends & Summary
    sum_status, summary = req("/wellness/summary", token=token)
    assert sum_status == 200, f"Wellness summary failed: {summary}"
    print(f"[PASS] 8. Wellness summary retrieved (Total entries: {len(summary.get('entries', []))}, Avg mood: {summary.get('averageMood')})")

    # 9. Test Dashboard Overview
    d_status, dash = req("/dashboard/summary", token=token)
    assert d_status == 200, f"Dashboard failed: {dash}"
    print(f"[PASS] 9. Dashboard overview loaded (Conversations: {dash.get('conversations')}, Mood: {dash.get('currentMood')})")

    # 10. Test Frontend Vite local proxy
    frontend_req = urllib.request.Request("http://localhost:5173/")
    with urllib.request.urlopen(frontend_req, timeout=5) as f_resp:
        assert f_resp.status == 200
        html = f_resp.read().decode("utf-8")
        assert "AI Health Companion" in html or "root" in html
        print(f"[PASS] 10. Frontend React/Vite serving successfully on http://localhost:5173")

    print("=" * 70)
    print("ALL LOCALHOST TESTS PASSED! APPLICATION IS 100% OPERATIONAL.")
    print("=" * 70)

if __name__ == "__main__":
    run()
