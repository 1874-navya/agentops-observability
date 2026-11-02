"""Initial trace and span storage."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "traces",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("agent_name", sa.String(255)),
        sa.Column("status", sa.String(32), nullable=False, server_default="unset"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.CheckConstraint("input_tokens >= 0 AND output_tokens >= 0 AND total_tokens >= 0"),
    )
    op.create_index("ix_traces_started_at", "traces", ["started_at"])
    op.create_index("ix_traces_status_started", "traces", ["status", "started_at"])
    op.create_table(
        "spans",
        sa.Column("trace_id", sa.String(64), sa.ForeignKey("traces.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("span_id", sa.String(64), primary_key=True),
        sa.Column("parent_span_id", sa.String(64)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, server_default="custom"),
        sa.Column("status", sa.String(32), nullable=False, server_default="unset"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Float()),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model", sa.String(128)),
        sa.Column("provider", sa.String(128)),
        sa.Column("error_type", sa.String(255)),
        sa.Column("error_message", sa.Text()),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default="{}"),
        sa.CheckConstraint("input_tokens >= 0 AND output_tokens >= 0 AND total_tokens >= 0"),
    )
    op.create_index("ix_spans_trace_started", "spans", ["trace_id", "started_at"])
    op.create_index("ix_spans_kind_status", "spans", ["kind", "status"])


def downgrade() -> None:
    op.drop_index("ix_spans_kind_status", table_name="spans")
    op.drop_index("ix_spans_trace_started", table_name="spans")
    op.drop_table("spans")
    op.drop_index("ix_traces_status_started", table_name="traces")
    op.drop_index("ix_traces_started_at", table_name="traces")
    op.drop_table("traces")
