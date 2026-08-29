"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-29
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aegis_sbom",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("repo", sa.String(512), nullable=False),
        sa.Column("component_name", sa.String(512), nullable=False),
        sa.Column("version", sa.String(128), nullable=False),
        sa.Column("purl", sa.String(1024), nullable=False),
        sa.Column("ecosystem", sa.String(64), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("repo", "purl", name="uq_aegis_sbom_repo_purl"),
    )
    op.create_index("ix_aegis_sbom_purl", "aegis_sbom", ["purl"])
    op.create_index("ix_aegis_sbom_ecosystem", "aegis_sbom", ["ecosystem"])
    op.create_index("ix_aegis_sbom_component", "aegis_sbom", ["component_name"])

    op.create_table(
        "aegis_sbom_licenses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("purl", sa.String(1024), nullable=False),
        sa.Column("license", sa.String(256), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "purl", "source", name="uq_aegis_sbom_licenses_purl_source"
        ),
    )
    op.create_index("ix_aegis_sbom_licenses_purl", "aegis_sbom_licenses", ["purl"])

    op.create_table(
        "aegis_purl_license_cache",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("purl", sa.String(1024), nullable=False, unique=True),
        sa.Column("license", sa.String(256), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ecosystem", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_aegis_purl_license_cache_purl",
        "aegis_purl_license_cache",
        ["purl"],
        unique=True,
    )

    op.create_table(
        "aegis_news",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(1024), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False, unique=True),
        sa.Column("source", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("body_text", sa.Text, nullable=True),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("affected_packages", sa.JSON, nullable=True),
        sa.Column("impact_score", sa.Integer, nullable=True),
        sa.Column("slack_ts", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_aegis_news_url", "aegis_news", ["url"], unique=True)
    op.create_index("ix_aegis_news_classification", "aegis_news", ["classification"])
    op.create_index("ix_aegis_news_created_at", "aegis_news", ["created_at"])

    op.create_table(
        "aegis_feed_state",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("feed_url", sa.String(2048), nullable=False, unique=True),
        sa.Column("etag", sa.String(256), nullable=True),
        sa.Column("last_modified", sa.String(128), nullable=True),
        sa.Column("high_water_mark", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(128), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_aegis_feed_state_feed_url",
        "aegis_feed_state",
        ["feed_url"],
        unique=True,
    )

    op.create_table(
        "aegis_match_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "news_id",
            sa.Integer,
            sa.ForeignKey("aegis_news.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("repo", sa.String(512), nullable=False),
        sa.Column("component_name", sa.String(512), nullable=False),
        sa.Column("version_in_use", sa.String(128), nullable=False),
        sa.Column("vulnerable_versions", sa.String(512), nullable=False),
        sa.Column("is_vulnerable", sa.Boolean, nullable=False),
        sa.Column("purl", sa.String(1024), nullable=False),
        sa.Column("ecosystem", sa.String(64), nullable=False),
        sa.Column(
            "matched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_aegis_match_result_news_id", "aegis_match_result", ["news_id"])
    op.create_index("ix_aegis_match_result_repo", "aegis_match_result", ["repo"])


def downgrade() -> None:
    op.drop_table("aegis_match_result")
    op.drop_table("aegis_feed_state")
    op.drop_table("aegis_news")
    op.drop_table("aegis_purl_license_cache")
    op.drop_table("aegis_sbom_licenses")
    op.drop_table("aegis_sbom")
