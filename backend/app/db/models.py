from sqlalchemy import Column, String, DateTime, Enum, Text, Integer, ForeignKey, JSON, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    FAN = "fan"
    VOLUNTEER = "volunteer"
    OPERATOR = "operator"
    EMERGENCY = "emergency"


class AccessibilityNeed(str, enum.Enum):
    WHEELCHAIR = "wheelchair"
    AVOID_STAIRS = "avoid_stairs"
    LOW_MOBILITY = "low_mobility"
    VISUAL_IMPAIRMENT = "visual_impairment"
    HEARING_IMPAIRMENT = "hearing_impairment"
    NONE = "none"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.FAN)
    preferred_language = Column(String(10), default="en")
    accessibility_needs = Column(JSON, default=list)
    ticket_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chat_sessions = relationship("ChatSession", back_populates="user")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    language = Column(String(10), default="en")
    context = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    metadata = Column(JSON, default=dict)
    agent_used = Column(String(50), nullable=True)
    sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class Gate(Base):
    __tablename__ = "gates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    level = Column(Integer, default=0)
    section = Column(String(50), nullable=True)
    capacity = Column(Integer, default=0)
    status = Column(String(20), default="open")
    accessibility_features = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrowdSnapshot(Base):
    __tablename__ = "crowd_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id = Column(String(50), ForeignKey("gates.gate_id"), nullable=False, index=True)
    current_count = Column(Integer, default=0)
    density_percentage = Column(Float, default=0.0)
    trend = Column(String(20), default="stable")
    estimated_wait_minutes = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    gate = relationship("Gate")

    __table_args__ = (
        Index("ix_crowd_snapshots_gate_time", "gate_id", "timestamp"),
    )


class EmergencyIncident(Base):
    __tablename__ = "emergency_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    reported_by = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    response_plan = Column(JSON, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(JSON, default=list)
    language = Column(String(10), default="en")
    source = Column(String(200), nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NavigationRoute(Base):
    __tablename__ = "navigation_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_gate = Column(String(50), nullable=False)
    destination_gate = Column(String(50), nullable=False)
    accessibility_profile = Column(JSON, default=list)
    path_geojson = Column(JSON, nullable=False)
    distance_meters = Column(Float, nullable=False)
    estimated_time_seconds = Column(Integer, nullable=False)
    crowd_adjusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_navigation_routes_origin_dest", "origin_gate", "destination_gate"),
    )


class OperationalMetric(Base):
    __tablename__ = "operational_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default=dict)

    __table_args__ = (
        Index("ix_operational_metrics_name_time", "metric_name", "timestamp"),
    )