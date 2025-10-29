from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), unique=True, index=True)
    court_id = Column(String(32), index=True)
    location_region = Column(String(64))
    case_type = Column(String(64))
    filing_date = Column(Date)
    resolution_date = Column(Date, nullable=True)
    num_hearings = Column(Integer, default=0)
    num_adjournments = Column(Integer, default=0)
    judge_id_hashed = Column(String(64))
    outcome_category = Column(String(32), nullable=True)
    time_to_resolution_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Hearing(Base):
    __tablename__ = "hearings"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), index=True)
    hearing_id = Column(String(64), unique=True, index=True)
    hearing_date = Column(Date)
    hearing_outcome = Column(String(32))  # "proceeded" or "adjourned"
    adjournment_reason = Column(String(128), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Court(Base):
    __tablename__ = "courts"
    
    id = Column(Integer, primary_key=True, index=True)
    court_id = Column(String(32), unique=True, index=True)
    name = Column(String(128))
    region = Column(String(64))
    location_district = Column(String(128))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
