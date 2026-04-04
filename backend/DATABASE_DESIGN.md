# Database design

This document describes the database schema for the SafeRoute anonymous security incident reporting application. It covers the entity-relationship model, detailed table specifications, design decisions, and implementation guidance for the SQLAlchemy models and Alembic migrations.

## Entity-relationship diagram (DBML)

```dbml
Project safe_route {
  database_type: 'PostgreSQL'
  description: '''
    ER diagram for the SafeRoute anonymous
    security incident reporting application.
  '''
}

Enum safe_route.report_status {
  pending
  under_review
  approved
  resolved
}

Enum safe_route.user_role {
  admin
  editor
  reporter
}

Enum safe_route.media_type {
  image
  video
  audio
}

Enum safe_route.severity_level {
  low
  medium
  high
}

Enum safe_route.audit_action {
  created
  status_changed
  severity_changed
  assigned
  approved
  description_edited
  media_added
  media_removed
}

Enum safe_route.actor_type {
  user
  anonymous
  system
}

Table safe_route.app_user {
  id uuid [pk, default: `gen_random_uuid()`]
  first_name varchar [not null]
  last_name varchar [not null]
  email varchar [not null, unique]
  role user_role [not null, default: 'reporter']
  hashed_password varchar [not null]
  is_active boolean [not null, default: true]
  created_at timestamptz [not null, default: `now()`]
  updated_at timestamptz [not null, default: `now()`]
}

Table safe_route.location {
  id uuid [pk, default: `gen_random_uuid()`]
  state varchar [not null]
  city varchar [not null]
  town varchar
  created_at timestamptz [not null, default: `now()`]
}

Table safe_route.report {
  id uuid [pk, default: `gen_random_uuid()`]
  reporter_id uuid [ref: > safe_route.app_user.id, note: 'null for anonymous submissions']
  location_id uuid [not null, ref: > safe_route.location.id]
  approver_id uuid [ref: > safe_route.app_user.id]
  reference_no varchar(12) [not null, unique, note: 'issued to reporter for status tracking']
  status report_status [not null, default: 'pending']
  severity severity_level [not null, default: 'low']
  description text [not null]
  incident_at timestamptz [not null]
  approval_date timestamptz
  is_deleted boolean [not null, default: false]
  created_at timestamptz [not null, default: `now()`]
  updated_at timestamptz [not null, default: `now()`]

  indexes {
    reporter_id
    location_id
    status
    severity
    incident_at
    reference_no
  }
}

Table safe_route.media {
  id uuid [pk, default: `gen_random_uuid()`]
  report_id uuid [not null, ref: > safe_route.report.id]
  type media_type [not null]
  media_link varchar [not null]
  created_at timestamptz [not null, default: `now()`]
}

Table safe_route.report_audit_log {
  id uuid [pk, default: `gen_random_uuid()`]
  report_id uuid [not null, ref: > safe_route.report.id]
  actor_id uuid [ref: > safe_route.app_user.id, note: 'null when actor is anonymous or system']
  actor_type actor_type [not null, default: 'user']
  action audit_action [not null]
  old_value varchar
  new_value varchar
  note text
  created_at timestamptz [not null, default: `now()`]

  indexes {
    report_id
    actor_id
    created_at
  }
}
```

## Table design notes

### `app_user`

This table represents internal platform users only: admins, editors, and reporters who choose to create accounts. Anonymous submitters never appear here.

The `email` unique constraint serves as the login identifier. `is_active` is for soft-deactivation a deactivated user cannot log in, but their audit trail and report associations remain intact. Never hard-delete user rows, since that would orphan foreign key references across `report` and `report_audit_log`.

The `hashed_password` column must store bcrypt or argon2id output, never plaintext. In the SQLAlchemy model, this column should have no default and must be set explicitly through the auth service layer.

`updated_at` should be maintained via a SQLAlchemy `onupdate=func.now()` column hook or a PostgreSQL trigger on row mutation. Do not rely on the application to set this manually.

The table is named `app_user` rather than `user` to avoid collisions with the PostgreSQL reserved word, which would require quoting in every query.

### `location`

A normalised lookup table for incident locations. The assumption is that locations are reusable: multiple reports can reference the same state/city/town combination. Before inserting a new report, the service layer should check for an existing location match to avoid duplicates. If the submission UI uses free-text location input rather than a dropdown, implement a deduplication strategy — either exact-match lookups or a normalisation step (lowercase, strip whitespace) before insertion.

`town` is nullable because not every incident will have town-level granularity.

If the team later wants map-based pinpointing, add a PostGIS `geography(Point, 4326)` column here rather than separate latitude/longitude floats, since PostGIS provides spatial indexing and distance queries out of the box.

There is no `updated_at` column because location records should be treated as immutable once created. If a location was entered incorrectly, create a new record and update the report's `location_id` rather than mutating the location in place — other reports may reference the same location row.

### `report`

The central entity in the schema.

`reporter_id` is nullable to support anonymous submissions, which is the application's primary use case. When null, `reference_no` is the reporter's only way to track their submission. Because `reference_no` effectively functions as an access credential for anonymous reporters, it must be generated using a cryptographically secure method such as `secrets.token_urlsafe` in Python, not a sequential or predictable pattern like `SR-0001`. A predictable format would allow enumeration attacks against the tracking endpoint. A suggested format is a short prefix plus random characters, such as `SR-a8Kf3xQm`, which gives readability alongside sufficient entropy.

`approver_id` is null until a reviewer explicitly approves or resolves the report. `approval_date` is set at the same time as `approver_id` — both should be written in the same transaction.

`severity` defaults to `low` and can be escalated by reviewers. The severity levels map to the UI colour codes: `low` = yellow, `medium` = orange, `high` = red. Every severity change must produce a corresponding entry in `report_audit_log`.

`is_deleted` enables soft deletion. The application layer should filter `is_deleted = false` by default on all queries, ideally through a SQLAlchemy query event hook, a default query scope, or a helper method on the repository base class. Hard deletion of report rows is not permitted, since audit log entries reference the report by foreign key.

`incident_at` is a single `timestamptz` column combining the date and time of the incident. Do not split this into separate date and time columns a single timestamp is simpler, avoids inconsistency between the two values, and supports timezone-aware storage. If date-only filtering is needed for the dashboard, extract the date from the timestamp at query time.

The indexes cover the most common query patterns:
    1. filtering by `status` and `severity` on the reviewer dashboard
    2. looking up by `reference_no` for the anonymous tracking endpoint
    3. filtering by `location_id` for geographic analysis
    4. range queries on `incident_at` for time-based reporting

### `media`

Stores metadata for files attached to a report. The actual files live in object storage (S3, MinIO, or equivalent), not in the database. `media_link` holds the object URL or storage key.

A report can have zero or many media attachments. The foreign key lives here on `media`, not on `report` this is a one-to-many relationship with `report` as the parent. There is no back-reference column on `report`.

The `type` enum constrains uploads to known categories (`image`, `video`, `audio`), which helps the frontend render the appropriate preview component and allows the backend to apply type-specific validation rules (file size limits, MIME type checking).

Consider adding a `file_size_bytes bigint` column if upload limits need to be enforced or tracked at the database level in addition to the application layer.

This table has no `updated_at` column because media records should be immutable once created. If a file needs to be replaced, the service layer should delete the old row and insert a new one, logging both a `media_removed` and a `media_added` action in the audit trail within the same transaction. The old file should also be deleted from object storage, either synchronously or via a background cleanup task.

### `report_audit_log`

The append-only event ledger that powers the reviewer dashboard's audit trail.

**This table is strictly insert-only. No updates. No deletes. Ever.** This invariant is critical for audit integrity and must be enforced at multiple levels:

1. **Repository layer:** The `ReportAuditLogRepository` should expose only a `create` method. Do not implement `update`, `delete`, or any bulk mutation method. This is the primary enforcement mechanism.
2. **Database layer (recommended):** As a belt-and-suspenders measure, create a PostgreSQL trigger that raises an exception on `UPDATE` or `DELETE` operations against this table. This protects against bugs or future code changes that bypass the repository.

```sql
CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'report_audit_log is append-only: % operations are not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_immutable
  BEFORE UPDATE OR DELETE ON report_audit_log
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
```

`actor_id` is nullable to handle two cases: actions performed by anonymous reporters (such as the initial `created` event on an anonymous submission) and system-generated events (such as an automatic escalation rule or a scheduled status transition). The `actor_type` enum (`user`, `anonymous`, `system`) distinguishes between these cases, so the reviewer dashboard can display the appropriate attribution — a reviewer's name, "Anonymous reporter," or "System."

`old_value` and `new_value` are generic varchar columns that store the before/after state as strings. For a status change, this would be `old_value: 'pending'`, `new_value: 'under_review'`; for a severity change, `old_value: 'low'`, `new_value: 'high'`. This is intentionally denormalised — storing values as strings rather than foreign key references makes the audit log self-contained and queryable without joins to the source tables. A viewer of the audit log should be able to reconstruct the full history of a report from the log alone.

`note` is an optional free-text field for reviewer comments explaining why they made a change. The UI likely renders this as a comment alongside the audit entry in the reviewer dashboard.

**Transactional consistency:** Every mutation to a report — status, severity, assignment, description edit, media add, media remove — must produce exactly one audit log row in the same database transaction as the mutation itself. If the transaction rolls back, the audit entry rolls back with it. Never write audit entries in a separate transaction or as a fire-and-forget side effect. In the FastAPI service layer, this means the report update and audit log insert share the same `AsyncSession` and are committed together.

The primary query pattern for this table is `SELECT * FROM report_audit_log WHERE report_id = :id ORDER BY created_at DESC`, which renders the chronological trail on the reviewer dashboard. The `actor_id` join to `app_user` provides "who did it," and `old_value`/`new_value` provides "what changed."

## Design decisions

### Why anonymous submissions use nullable `reporter_id`

Since the submission screen does not require any personal information, the application's primary use case is anonymous reporting. Rather than requiring a throwaway account or session, `reporter_id` is simply null for anonymous submissions. The `reference_no` column serves as the anonymous reporter's handle for tracking their report status. This is the simplest model that fully supports anonymity without introducing phantom user records or session tokens.

### Why `reference_no` doubles as the tracking credential

The Figma designs show that `reference_no` is the value presented to the user for tracking their report. Rather than introducing a separate `tracking_token` column, `reference_no` serves both as the internal reference and the external tracking handle. This avoids redundancy but requires that the value is generated securely — see the notes on the `report` table above.

### Why the audit log uses generic `old_value`/`new_value` strings

A more normalised approach would use typed columns or separate tables per action type. The generic string approach trades type safety for simplicity and flexibility: new audit actions can be added without schema changes, and the log is fully self-contained without requiring joins to interpret the history. For a reporting application where the audit trail is primarily for human review on a dashboard, this tradeoff is appropriate.
