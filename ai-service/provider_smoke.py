import io
import json
import urllib.request
import uuid

from PIL import Image

base = "http://localhost:8080"
email = f"provider-{uuid.uuid4().hex}@example.local"
register = urllib.request.Request(
    f"{base}/api/auth/register",
    data=json.dumps({"name": "Provider Check", "email": email, "password": "HealthCheck123!", "confirmPassword": "HealthCheck123!"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
token = json.load(urllib.request.urlopen(register))["token"]

image = io.BytesIO()
Image.new("RGB", (32, 32), (220, 120, 40)).save(image, format="PNG")
boundary = "----HealthCompanionBoundary"
body = (
    f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="produce.png"\r\n'
    "Content-Type: image/png\r\n\r\n"
).encode() + image.getvalue() + f"\r\n--{boundary}--\r\n".encode()
analyze = urllib.request.Request(
    f"{base}/api/food/analyze", data=body,
    headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
result = json.load(urllib.request.urlopen(analyze))
print(json.dumps({key: result.get(key) for key in ("foodName", "freshnessScore", "condition", "mock", "observations")}))
