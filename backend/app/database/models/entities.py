from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # Null for dev-mock logins (no real Google account involved).
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class StudentProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "student_profiles"

    # Nullable: profiles created before auth existed (or without logging in)
    # remain valid; new profiles are linked to the authenticated user when
    # a valid session is present.
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    academic_level: Mapped[str | None] = mapped_column(String(100))
    current_degree: Mapped[str | None] = mapped_column(String(255))
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    university: Mapped[str | None] = mapped_column(String(255))
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    target_degree: Mapped[str | None] = mapped_column(String(100))
    target_countries: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    research_interests: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    publications: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    projects: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    work_experience: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    preferred_funding: Mapped[str | None] = mapped_column(String(255))


class University(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "universities"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(100))
    website_url: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)


class Professor(UUIDMixin, Base):
    __tablename__ = "professors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    university: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    research_interests: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    publications: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    profile_url: Mapped[str | None] = mapped_column(String(512))
    email: Mapped[str | None] = mapped_column(String(255))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)


class Program(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "programs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    university_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("universities.id"), nullable=True)
    degree_level: Mapped[str | None] = mapped_column(String(100))
    field: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)


class Opportunity(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "opportunities"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider: Mapped[str | None] = mapped_column(String(255))
    university: Mapped[str | None] = mapped_column(String(255))
    degree_level: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    field: Mapped[str | None] = mapped_column(String(255))
    funding_type: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    eligibility: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    application_url: Mapped[str | None] = mapped_column(String(512))
    source_url: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)


class Application(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=True)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(UUIDMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    document = relationship("Document", back_populates="chunks")


class SOPDocument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sop_documents"

    profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    draft_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(100), default="draft", nullable=False)


class WorkflowExecution(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workflow_executions"

    profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)

    agent_executions = relationship("AgentExecution", back_populates="workflow", cascade="all, delete-orphan")
    messages = relationship("AgentMessage", back_populates="workflow", cascade="all, delete-orphan")


class AgentExecution(UUIDMixin, Base):
    __tablename__ = "agent_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="success")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    token_usage: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)

    workflow = relationship("WorkflowExecution", back_populates="agent_executions")


class AgentMessage(UUIDMixin, Base):
    __tablename__ = "agent_messages"

    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(100), nullable=False)
    receiver: Mapped[str] = mapped_column(String(100), nullable=False)
    message_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    workflow = relationship("WorkflowExecution", back_populates="messages")


class Memory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memory_entries"
    __table_args__ = (UniqueConstraint("profile_id", "memory_type", "scope", name="uq_memory_profile_type_scope"),)

    profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=True)
    memory_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(100), nullable=False, default="short_term")
    content: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
