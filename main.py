from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import joblib
import numpy as np

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# ---------------------------
# ✅ Initialize FastAPI app
# ---------------------------
app = FastAPI(title="Diabetes Prediction API with CRUD & Gender")

# ---------------------------
# ✅ Load model & scaler
# ---------------------------
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500"] if using Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = joblib.load('diabetes_model.pkl')
    scaler = joblib.load('scaler.pkl')
    print("[INFO] Model & scaler loaded successfully.")
except Exception as e:
    print(f"[ERROR] Could not load model/scaler: {e}")

# ---------------------------
# ✅ PostgreSQL Database setup
# ---------------------------
DATABASE_URL = "postgresql://postgres:12345@localhost:5432/diabetesdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------------------
# ✅ Define DB Table
# ---------------------------
class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    gender = Column(String)
    pregnancies = Column(Integer)
    glucose = Column(Float)
    blood_pressure = Column(Float)
    skin_thickness = Column(Float)
    insulin = Column(Float)
    bmi = Column(Float)
    diabetes_pedigree = Column(Float)
    age = Column(Integer)
    prediction = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ---------------------------
# ✅ Pydantic schemas
# ---------------------------
class PatientData(BaseModel):
    gender: str = Field(..., regex="^(male|female)$")
    pregnancies: int = Field(..., ge=0)
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree: float
    age: int

class LogResponse(BaseModel):
    id: int
    gender: str
    pregnancies: int
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree: float
    age: int
    prediction: int
    timestamp: datetime

class UpdateLog(BaseModel):
    pregnancies: int
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree: float
    age: int

# ---------------------------
# ✅ API Routes
# ---------------------------
@app.get("/")
def read_root():
    return {"status": "success", "message": "✅ Diabetes Prediction API is running."}

@app.post("/predict", response_model=dict)
def predict(data: PatientData):
    try:
        pregnancies = data.pregnancies
        if data.gender.lower() == "male":
            pregnancies = 0

        input_data = np.array([[ 
            pregnancies,
            data.glucose,
            data.blood_pressure,
            data.skin_thickness,
            data.insulin,
            data.bmi,
            data.diabetes_pedigree,
            data.age
        ]])

        input_scaled = scaler.transform(input_data)
        prediction = model.predict(input_scaled)
        prediction_result = int(prediction[0])

        with SessionLocal() as db:
            log_entry = PredictionLog(
                gender=data.gender.lower(),
                pregnancies=pregnancies,
                glucose=data.glucose,
                blood_pressure=data.blood_pressure,
                skin_thickness=data.skin_thickness,
                insulin=data.insulin,
                bmi=data.bmi,
                diabetes_pedigree=data.diabetes_pedigree,
                age=data.age,
                prediction=prediction_result
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

        result = "Positive for Diabetes" if prediction_result == 1 else "Negative for Diabetes"
        return {
            "status": "success",
            "message": "Prediction successful.",
            "data": {
                "prediction": prediction_result,
                "result": result,
                "log_id": log_entry.id
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

@app.get("/logs", response_model=List[LogResponse])
def get_logs():
    with SessionLocal() as db:
        logs = db.query(PredictionLog).all()
        return logs

@app.put("/logs/{log_id}", response_model=dict)
def update_log(log_id: int, log_data: UpdateLog):
    with SessionLocal() as db:
        log = db.query(PredictionLog).filter(PredictionLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

        log.pregnancies = log_data.pregnancies
        log.glucose = log_data.glucose
        log.blood_pressure = log_data.blood_pressure
        log.skin_thickness = log_data.skin_thickness
        log.insulin = log_data.insulin
        log.bmi = log_data.bmi
        log.diabetes_pedigree = log_data.diabetes_pedigree
        log.age = log_data.age

        db.commit()
        db.refresh(log)
        return {
            "status": "success",
            "message": f"Log {log_id} updated successfully.",
            "updated_log_id": log.id
        }

@app.delete("/logs/{log_id}", response_model=dict)
def delete_log(log_id: int):
    with SessionLocal() as db:
        log = db.query(PredictionLog).filter(PredictionLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

        db.delete(log)
        db.commit()
        return {
            "status": "success",
            "message": f"Log {log_id} deleted successfully."
        }
