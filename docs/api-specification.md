# REST API specification

Base URL: `/api`  
Media type: `application/json` except food image upload (`multipart/form-data`).  
Authenticated routes require `Authorization: Bearer <JWT>` beginning in Phase 2.

## Phase 1 implemented

| Method | Route | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/status` | Public | Verify the frontend-to-backend connection and report the explicit AI mode. |

Example response:

```json
{
  "status": "available",
  "application": "AI Health Companion API",
  "aiMode": "mock",
  "timestamp": "2026-09-22T10:30:00Z"
}
```

## Planned resource contract

| Area | Method and route | Request / response intent |
| --- | --- | --- |
| Auth | `POST /auth/register` | Validated name, email, password and confirmation → profile plus access token. |
| Auth | `POST /auth/login` | Email and password → profile plus access token. |
| User | `GET`, `PUT /users/profile` | Read or edit the authenticated user’s safe profile fields. |
| Food | `POST /food/analyze` | Multipart `image` → persisted visible-condition analysis plus limitations. |
| Food | `GET /food/history`, `GET`, `DELETE /food/{id}` | Paginated own scan history; single own scan; delete own scan. |
| Chat | `POST`, `GET /chat/conversations` | Create/list only the requester’s conversations. |
| Chat | `POST`, `GET /chat/conversations/{id}/messages` | Add/list messages after conversation-ownership verification. |
| Chat | `DELETE /chat/conversations/{id}` | Delete only an owned conversation. |
| Wellness | `POST /wellness/check-in` | Mood, stress and energy 1–10; bounded sleep hours; optional journal text. |
| Wellness | `GET /wellness/history`, `/wellness/summary`, `/wellness/trends` | Return own entries, aggregates and non-diagnostic observations. |

## API conventions

- DTOs—not JPA entities—cross the API boundary.
- `201 Created` includes a `Location` header for creation; `204 No Content` for successful deletion.
- Validation failures use `400`; absent/invalid credentials use `401`; ownership failures resolve as `404` to avoid record enumeration; conflicts such as duplicate email use `409`.
- Provider outages return a safe `503` response with a user-friendly code, never provider stack traces or secret details.
