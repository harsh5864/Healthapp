# Database design and ER diagram description

The schema will be introduced with JPA entities in Phases 2–6. All temporal values use UTC `Instant`/`TIMESTAMP`, and all feature records are user-owned.

```mermaid
erDiagram
    USER ||--o{ FOOD_SCAN : owns
    USER ||--o{ CHAT_CONVERSATION : owns
    CHAT_CONVERSATION ||--o{ CHAT_MESSAGE : contains
    USER ||--o{ WELLNESS_ENTRY : records
    USER ||--o{ WELLNESS_ANALYSIS : receives

    USER {
        bigint id PK
        varchar name
        varchar email UK
        varchar password_hash
        datetime created_at
        datetime updated_at
    }
    FOOD_SCAN {
        bigint id PK
        bigint user_id FK
        varchar image_url
        varchar food_name
        int freshness_score
        varchar condition
        text observations
        text recommendation
        datetime created_at
    }
    CHAT_CONVERSATION {
        bigint id PK
        bigint user_id FK
        varchar title
        datetime created_at
        datetime updated_at
    }
    CHAT_MESSAGE {
        bigint id PK
        bigint conversation_id FK
        varchar sender
        text message
        datetime timestamp
    }
    WELLNESS_ENTRY {
        bigint id PK
        bigint user_id FK
        tinyint mood
        tinyint stress
        tinyint energy
        decimal sleep_hours
        text journal_text
        datetime created_at
    }
    WELLNESS_ANALYSIS {
        bigint id PK
        bigint user_id FK
        text analysis
        varchar mood_trend
        varchar stress_trend
        varchar sleep_trend
        datetime created_at
    }
```

## Integrity and privacy rules

- `user.email` has a unique, case-normalized index.
- All child foreign keys are non-null and indexed. Conversations cascade to their messages only when the owner deletes the conversation.
- User data queries always constrain by the authenticated `user_id`; an ID alone is never sufficient authorization.
- Passwords use BCrypt hashes. Uploaded images are stored outside the database or in managed object storage; only a safe reference is persisted.
- Wellness entries are self-reported measurements, not clinical records or diagnoses.
