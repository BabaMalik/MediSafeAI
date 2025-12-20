"""
Patient Data Models
Database models for patient information, vitals, and disease progression
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from src.models.base import Base


class Patient(Base):
    """
    Patient demographic and condition information
    """
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(1), nullable=False)  # M or F
    dob = Column(Date, nullable=False)
    age = Column(Integer, nullable=False)
    zip_code = Column(String(10), nullable=False)
    income = Column(Float, nullable=False)
    insurance = Column(String(20), nullable=False)

    # Pre-existing conditions
    diabetes = Column(Boolean, default=False)
    hypertension = Column(Boolean, default=False)
    heart_disease = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    vitals = relationship("PatientVitals", back_populates="patient", cascade="all, delete-orphan")
    progression = relationship("PatientProgression", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient {self.patient_id}: {self.first_name} {self.last_name}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'patient_id': self.patient_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'gender': self.gender,
            'dob': self.dob.isoformat() if self.dob else None,
            'age': self.age,
            'zip_code': self.zip_code,
            'income': self.income,
            'insurance': self.insurance,
            'diabetes': self.diabetes,
            'hypertension': self.hypertension,
            'heart_disease': self.heart_disease,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PatientVitals(Base):
    """
    Patient vital signs and measurements
    """
    __tablename__ = 'patient_vitals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(20), ForeignKey('patients.patient_id'), nullable=False, index=True)

    # Vital signs
    blood_pressure_systolic = Column(Float, nullable=False)
    blood_pressure_diastolic = Column(Float, nullable=False)
    heart_rate = Column(Float, nullable=False)
    blood_glucose = Column(Float, nullable=False)
    cholesterol = Column(Float, nullable=False)
    body_temperature = Column(Float, nullable=False)
    respiratory_rate = Column(Float, nullable=False)
    oxygen_saturation = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)

    # Metadata
    measurement_date = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="vitals")

    def __repr__(self):
        return f"<PatientVitals {self.patient_id} on {self.measurement_date}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'patient_id': self.patient_id,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'heart_rate': self.heart_rate,
            'blood_glucose': self.blood_glucose,
            'cholesterol': self.cholesterol,
            'body_temperature': self.body_temperature,
            'respiratory_rate': self.respiratory_rate,
            'oxygen_saturation': self.oxygen_saturation,
            'weight': self.weight,
            'measurement_date': self.measurement_date.isoformat() if self.measurement_date else None,
        }


class PatientProgression(Base):
    """
    Disease progression tracking over time
    """
    __tablename__ = 'patient_progression'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(20), ForeignKey('patients.patient_id'), nullable=False, index=True)

    # Visit information
    visit_number = Column(Integer, nullable=False)
    visit_date = Column(Date, nullable=False)

    # Vital signs at visit
    blood_pressure_systolic = Column(Float)
    blood_pressure_diastolic = Column(Float)
    heart_rate = Column(Float)
    blood_glucose = Column(Float)
    weight = Column(Float)

    # Lab measurements
    hemoglobin_a1c = Column(Float)
    white_blood_cells = Column(Float)
    creatinine = Column(Float)

    # Disease-specific metrics
    insulin_level = Column(Float, nullable=True)  # For diabetes
    ejection_fraction = Column(Float, nullable=True)  # For heart disease
    troponin = Column(Float, nullable=True)  # For heart disease

    # Intervention tracking
    intervention_occurred = Column(Boolean, default=False)
    intervention_type = Column(String(50), nullable=True)
    intervention_notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="progression")

    def __repr__(self):
        return f"<PatientProgression {self.patient_id} visit {self.visit_number}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'patient_id': self.patient_id,
            'visit_number': self.visit_number,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'blood_pressure_systolic': self.blood_pressure_systolic,
            'blood_pressure_diastolic': self.blood_pressure_diastolic,
            'heart_rate': self.heart_rate,
            'blood_glucose': self.blood_glucose,
            'weight': self.weight,
            'hemoglobin_a1c': self.hemoglobin_a1c,
            'white_blood_cells': self.white_blood_cells,
            'creatinine': self.creatinine,
            'insulin_level': self.insulin_level,
            'ejection_fraction': self.ejection_fraction,
            'troponin': self.troponin,
            'intervention_occurred': self.intervention_occurred,
            'intervention_type': self.intervention_type,
        }
