import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TicketStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    resolved = "resolved"
    escalated = "escalated"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    customer_id = Column(String(100), nullable=True)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.pending, nullable=False)
    category = Column(String(50), nullable=True)
    urgency = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent_steps = relationship("AgentStep", back_populates="ticket", cascade="all, delete-orphan")
    resolution = relationship("Resolution", back_populates="ticket", uselist=False, cascade="all, delete-orphan")

class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    input_json = Column(Text, nullable=False)
    output_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="agent_steps")

class Resolution(Base):
    __tablename__ = "resolutions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), unique=True, nullable=False)
    decision = Column(String(50), nullable=False)
    matched_rule = Column(String(100), nullable=False)
    draft_response = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    reason = Column(Text, nullable=False)

    ticket = relationship("Ticket", back_populates="resolution")
