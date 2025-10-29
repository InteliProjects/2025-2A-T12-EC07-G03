from sqlalchemy import Column, String, Text, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .database import Base

class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_name = Column(String, nullable=False)
    indicator = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    start_date = Column(TIMESTAMP(timezone=True), nullable=True)
    end_date = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    bucket_address = Column(String, nullable=True)

class ProcessedData(Base):
    __tablename__ = "processed_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    motor_pump = Column(String, nullable=False)
    Auto = Column(Float, nullable=False)
    Bat_V = Column(Float, nullable=False)
    Char_V = Column(Float, nullable=False)
    Cool_T = Column(Float, nullable=False)
    Eng_RPM = Column(Float, nullable=False)
    Fuel_Con = Column(Float, nullable=False)
    Fuel_L = Column(Float, nullable=False)
    Man = Column(Float, nullable=False)
    Oil_L = Column(Float, nullable=False)
    Oil_P = Column(Float, nullable=False)
    Recalque = Column(Float, nullable=False)
    Starts_N = Column(Float, nullable=False)
    Stop = Column(Float, nullable=False)
    Succao = Column(Float, nullable=False)
    running = Column(Float, nullable=False)
    minutes_running = Column(Float, nullable=False)
    Bat_V_variation = Column(Float, nullable=False)
    Char_V_variation = Column(Float, nullable=False)
    Cool_T_variation = Column(Float, nullable=False)
    Eng_RPM_variation = Column(Float, nullable=False)
    Fuel_Con_variation = Column(Float, nullable=False)
    Fuel_L_variation = Column(Float, nullable=False)
    Oil_L_variation = Column(Float, nullable=False)
    Oil_P_variation = Column(Float, nullable=False)
    Bat_V_variation_percentage = Column(Float, nullable=False)
    Char_V_variation_percentage = Column(Float, nullable=False)
    Cool_T_variation_percentage = Column(Float, nullable=False)
    Eng_RPM_variation_percentage = Column(Float, nullable=False)
    Fuel_Con_variation_percentage = Column(Float, nullable=False)
    Fuel_L_variation_percentage = Column(Float, nullable=False)
    Oil_L_variation_percentage = Column(Float, nullable=False)
    Oil_P_variation_percentage = Column(Float, nullable=False)
    Hydraulic_Head = Column(Float, nullable=False)
    Head_per_RPM = Column(Float, nullable=False)
    Head_trend_per_minutes = Column(Float, nullable=False)
    OilP_per_RPM = Column(Float, nullable=False)
    CoolT_per_RPM = Column(Float, nullable=False)
    Fuel_rate = Column(Float, nullable=False)
    Fuel_efficiency = Column(Float, nullable=False)
    FlexAnalogue4_1 = Column(Float, nullable=False)
    FlexAnalogue4_2 = Column(Float, nullable=False)