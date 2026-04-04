"""add audit log immutability trigger

Revision ID: c3b2112c3218
Revises: 8c899f3e4507
Create Date: 2026-03-31 19:23:44.800118

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3b2112c3218"
down_revision: Union[str, Sequence[str], None] = "8c899f3e4507"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION safe_route.prevent_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'report_audit_log is append-only: % operations are not permitted', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_immutable
            BEFORE UPDATE OR DELETE ON safe_route.report_audit_log
            FOR EACH ROW EXECUTE FUNCTION safe_route.prevent_audit_log_mutation();
    """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS audit_log_immutable ON safe_route.report_audit_log"
    )
    op.execute("DROP FUNCTION IF EXISTS safe_route.prevent_audit_log_mutation()")
