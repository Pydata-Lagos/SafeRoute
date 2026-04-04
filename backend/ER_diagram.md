erDiagram
    app_user ||--o{ report : "submits (reporter_id)"
    app_user ||--o{ report : "approves (approver_id)"
    app_user ||--o{ report_audit_log : "performs"
    location ||--o{ report : "occurred at"
    report ||--o{ media : "has"
    report ||--o{ report_audit_log : "tracks"

    app_user {
        uuid id PK
        varchar first_name
        varchar last_name
        varchar email UK
        user_role role
        varchar hashed_password
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    location {
        uuid id PK
        varchar state
        varchar city
        varchar town
        timestamptz created_at
    }

    report {
        uuid id PK
        uuid reporter_id FK "nullable"
        uuid location_id FK
        uuid approver_id FK "nullable"
        varchar reference_no UK
        report_status status
        severity_level severity
        text description
        timestamptz incident_at
        timestamptz approval_date "nullable"
        boolean is_deleted
        timestamptz created_at
        timestamptz updated_at
    }

    media {
        uuid id PK
        uuid report_id FK
        media_type type
        varchar media_link
        timestamptz created_at
    }

    report_audit_log {
        uuid id PK
        uuid report_id FK
        uuid actor_id FK "nullable"
        actor_type actor_type
        audit_action action
        varchar old_value "nullable"
        varchar new_value "nullable"
        text note "nullable"
        timestamptz created_at
    }
