"""SQLAlchemy database models."""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between groups and personas
group_personas = Table(
    'group_personas',
    Base.metadata,
    Column('group_id', String, ForeignKey('groups.id')),
    Column('persona_id', String, ForeignKey('personas.id'))
)


class Group(Base):
    """Chat group model."""
    __tablename__ = 'groups'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    personas = relationship('Persona', secondary=group_personas, back_populates='groups')
    simulations = relationship('Simulation', back_populates='group')
    messages = relationship('Message', back_populates='group')


class Persona(Base):
    """Persona model."""
    __tablename__ = 'personas'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    persona_type = Column(String, default='user')
    system_prompt = Column(Text, nullable=False)
    description = Column(Text)
    tools = Column(Text)  # JSON string of available tools
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    groups = relationship('Group', secondary=group_personas, back_populates='personas')
    memories = relationship('Memory', back_populates='persona', cascade='all, delete-orphan')


class Memory(Base):
    """Memory model for personas."""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    persona_id = Column(String, ForeignKey('personas.id'), nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(String, default='short_term')  # short_term or long_term
    importance = Column(Float, default=0.5)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    persona = relationship('Persona', back_populates='memories')


class Simulation(Base):
    """Simulation model."""
    __tablename__ = 'simulations'
    
    id = Column(String, primary_key=True)
    group_id = Column(String, ForeignKey('groups.id'))
    name = Column(String, nullable=False)
    description = Column(Text)
    persona_ids = Column(Text)  # JSON string of persona IDs
    status = Column(String, default='created')  # created, running, paused, completed, failed
    simulation_type = Column(String, default='chat')
    max_turns = Column(Integer)
    turn_delay = Column(Float, default=1.0)
    allow_user_interruption = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    group = relationship('Group', back_populates='simulations')
    messages = relationship('Message', back_populates='simulation', cascade='all, delete-orphan')


class Message(Base):
    """Message model."""
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True)
    simulation_id = Column(String, ForeignKey('simulations.id'), nullable=False)
    group_id = Column(String, ForeignKey('groups.id'))
    persona_id = Column(String, ForeignKey('personas.id'))
    content = Column(Text, nullable=False)
    role = Column(String, default='persona')  # user, persona, system
    status = Column(String, default='completed')
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_to = Column(String)
    
    # Relationships
    simulation = relationship('Simulation', back_populates='messages')
    group = relationship('Group', back_populates='messages')

