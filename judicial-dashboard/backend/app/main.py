from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from datetime import datetime
import pandas as pd
import numpy as np
from typing import List, Optional
import os
from dotenv import load_dotenv
from app.services.ml_service import ml_service
from app.db import engine, get_db
from app.models.case import Base, Case
from sqlalchemy.orm import Session
import hashlib
from app.auth import authenticate_user, create_access_token, require_role
from fastapi.security import OAuth2PasswordRequestForm
from PyPDF2 import PdfReader
import pdfplumber
try:
    from pdf2image import convert_from_path
    import pytesseract
except Exception:
    convert_from_path = None
    pytesseract = None

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Judicial Analytics Dashboard API",
    description="Predictive analytics and case management for Ugandan Judiciary",
    version="1.0.0"
)
# Static files (serve uploads)
UPLOADS_ROOT = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOADS_ROOT, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_ROOT), name="uploads")

# Serve React frontend static files (for production)
STATIC_ROOT = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_ROOT):
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")

# CORS middleware
# Allow all origins in production, specific in dev
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENV") == "production" else CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables if not exist
Base.metadata.create_all(bind=engine)
@app.post("/api/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}


# Sample data for development
SAMPLE_CASES = [
    {
        "case_id": "CASE-001",
        "court_id": "HC-001",
        "location_region": "Central",
        "case_type": "Civil",
        "filing_date": "2023-01-15",
        "resolution_date": "2023-06-20",
        "num_hearings": 4,
        "num_adjournments": 2,
        "judge_id_hashed": "JUDGE-001",
        "outcome_category": "Settled",
        "time_to_resolution_days": 156
    },
    {
        "case_id": "CASE-002",
        "court_id": "MC-001",
        "location_region": "Northern",
        "case_type": "Criminal",
        "filing_date": "2023-02-10",
        "resolution_date": "2023-08-15",
        "num_hearings": 6,
        "num_adjournments": 3,
        "judge_id_hashed": "JUDGE-002",
        "outcome_category": "Convicted",
        "time_to_resolution_days": 186
    }
]

@app.get("/")
async def root():
    return {"message": "Judicial Analytics Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/cases")
async def get_cases(db: Session = Depends(get_db)):
    """Get all cases (from DB if available, else fallback to sample)."""
    try:
        db_cases = db.query(Case).limit(500).all()
        if db_cases:
            cases = [
                {
                    "case_id": c.case_id,
                    "court_id": c.court_id,
                    "location_region": c.location_region,
                    "case_type": c.case_type,
                    "filing_date": c.filing_date.isoformat() if c.filing_date else None,
                    "resolution_date": c.resolution_date.isoformat() if c.resolution_date else None,
                    "num_hearings": c.num_hearings,
                    "num_adjournments": c.num_adjournments,
                    "judge_id_hashed": c.judge_id_hashed,
                    "outcome_category": c.outcome_category,
                    "time_to_resolution_days": c.time_to_resolution_days,
                }
                for c in db_cases
            ]
            return {"cases": cases, "total": len(cases)}
    except Exception:
        pass
    return {"cases": SAMPLE_CASES, "total": len(SAMPLE_CASES)}

@app.get("/api/cases/{case_id}")
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get specific case by ID"""
    try:
        c = db.query(Case).filter(Case.case_id == case_id).first()
        if c:
            case = {
                "case_id": c.case_id,
                "court_id": c.court_id,
                "location_region": c.location_region,
                "case_type": c.case_type,
                "filing_date": c.filing_date.isoformat() if c.filing_date else None,
                "resolution_date": c.resolution_date.isoformat() if c.resolution_date else None,
                "num_hearings": c.num_hearings,
                "num_adjournments": c.num_adjournments,
                "judge_id_hashed": c.judge_id_hashed,
                "outcome_category": c.outcome_category,
                "time_to_resolution_days": c.time_to_resolution_days,
            }
            return {"case": case}
    except Exception:
        pass
    case = next((c for c in SAMPLE_CASES if c["case_id"] == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"case": case}

def _apply_filters(df: pd.DataFrame, start_date: Optional[str], end_date: Optional[str], regions: Optional[List[str]], case_types: Optional[List[str]]) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    # normalize dates
    if 'filing_date' in df.columns:
        df['filing_date'] = pd.to_datetime(df['filing_date'], errors='coerce')
    if 'resolution_date' in df.columns:
        df['resolution_date'] = pd.to_datetime(df['resolution_date'], errors='coerce')
    if start_date:
        try:
            sd = pd.to_datetime(start_date, errors='coerce')
            df = df[(df['filing_date'].isna()) | (df['filing_date'] >= sd)]
        except Exception:
            pass
    if end_date:
        try:
            ed = pd.to_datetime(end_date, errors='coerce')
            df = df[(df['filing_date'].isna()) | (df['filing_date'] <= ed)]
        except Exception:
            pass
    if regions and 'location_region' in df.columns:
        df = df[df['location_region'].isin(regions)]
    if case_types and 'case_type' in df.columns:
        df = df[df['case_type'].isin(case_types)]
    return df

def _split_list(param: Optional[str]) -> Optional[List[str]]:
    if not param:
        return None
    return [p.strip() for p in param.split(',') if p.strip()]

@app.get("/api/analytics/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None, description="Comma-separated regions"),
    case_type: Optional[str] = Query(None, description="Comma-separated case types"),
):
    """Get dashboard summary statistics from DB; fallback to sample."""
    try:
        records = db.query(Case).all()
        if records:
            # Build DataFrame from DB
            data = []
            for c in records:
                data.append({
                    "case_id": c.case_id,
                    "court_id": c.court_id,
                    "location_region": c.location_region,
                    "case_type": c.case_type,
                    "filing_date": c.filing_date,
                    "resolution_date": c.resolution_date,
                    "num_hearings": c.num_hearings,
                    "num_adjournments": c.num_adjournments,
                    "judge_id_hashed": c.judge_id_hashed,
                    "outcome_category": c.outcome_category,
                    "time_to_resolution_days": c.time_to_resolution_days,
                })
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame(SAMPLE_CASES)
    except Exception:
        df = pd.DataFrame(SAMPLE_CASES)

    # Apply filters
    df = _apply_filters(df, start_date, end_date, _split_list(region), _split_list(case_type))

    # Handle potential NaNs/empties
    def safe_mean(series):
        try:
            return int(pd.to_numeric(series, errors='coerce').dropna().mean()) if len(series) else 0
        except Exception:
            return 0

    total_cases = int(len(df))
    resolved_cases = int(df.get("resolution_date", pd.Series(dtype=object)).dropna().shape[0])
    summary = {
        "total_cases": total_cases,
        "avg_resolution_time": safe_mean(df.get("time_to_resolution_days", pd.Series(dtype=float))),
        "cases_by_type": df.get("case_type", pd.Series(dtype=str)).value_counts().to_dict(),
        "cases_by_region": df.get("location_region", pd.Series(dtype=str)).value_counts().to_dict(),
        "avg_hearings": safe_mean(df.get("num_hearings", pd.Series(dtype=float))),
        "avg_adjournments": safe_mean(df.get("num_adjournments", pd.Series(dtype=float))),
        "resolved_cases": resolved_cases,
        "disposal_rate": (resolved_cases / total_cases) if total_cases else 0.0,
    }

    return {"summary": summary}

@app.get("/api/analytics/time-series")
async def get_time_series(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
):
    """Monthly inflow and resolved counts based on filing/resolution dates."""
    try:
        records = db.query(Case).all()
        if not records:
            df = pd.DataFrame(SAMPLE_CASES)
        else:
            df = pd.DataFrame([
                {
                    "filing_date": c.filing_date,
                    "resolution_date": c.resolution_date,
                }
                for c in records
            ])
        # Apply filters
        df = _apply_filters(df, start_date, end_date, _split_list(region), _split_list(case_type))
        df["filing_month"] = pd.to_datetime(df.get("filing_date"), errors='coerce').dt.to_period('M')
        df["resolution_month"] = pd.to_datetime(df.get("resolution_date"), errors='coerce').dt.to_period('M')
        inflow = df.dropna(subset=["filing_month"]).groupby("filing_month").size()
        resolved = df.dropna(subset=["resolution_month"]).groupby("resolution_month").size()
        months = sorted(set(inflow.index.astype(str)).union(set(resolved.index.astype(str))))
        series = [{"month": m, "cases": int(inflow.get(m, 0)), "resolution": int(resolved.get(m, 0))} for m in months]
        return {"series": series}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time series failed: {str(e)}")

@app.get("/api/analytics/resolution-distribution")
async def get_resolution_distribution(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
):
    """Bucketized distribution of time_to_resolution_days."""
    try:
        records = db.query(Case.case_type, Case.location_region, Case.filing_date, Case.time_to_resolution_days).all()
        # Create DataFrame to filter
        df = pd.DataFrame(records, columns=['case_type', 'location_region', 'filing_date', 'time_to_resolution_days'])
        df = _apply_filters(df, start_date, end_date, _split_list(region), _split_list(case_type))
        values = [int(v) for v in df['time_to_resolution_days'].dropna().tolist()]
        if not values:
            values = [c.get("time_to_resolution_days") for c in SAMPLE_CASES if c.get("time_to_resolution_days") is not None]
        bins = [(0,30), (31,90), (91,180), (181,365), (366,99999)]
        labels = ["0-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"]
        counts = []
        for (lo, hi), label in zip(bins, labels):
            counts.append({"category": label, "count": int(sum(1 for v in values if v is not None and lo <= v <= hi))})
        return {"distribution": counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Distribution failed: {str(e)}")

@app.get("/api/analytics/court-performance")
async def get_court_performance(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
):
    """Resolution rate per court (resolved/total)."""
    try:
        records = db.query(Case.court_id, Case.location_region, Case.case_type, Case.filing_date, Case.resolution_date).all()
        if not records:
            df = pd.DataFrame(SAMPLE_CASES)
        else:
            df = pd.DataFrame(records, columns=['court_id','location_region','case_type','filing_date','resolution_date'])
        df = _apply_filters(df, start_date, end_date, _split_list(region), _split_list(case_type))
        tmp = list(zip(df.get('court_id').fillna('Unknown'), df.get('resolution_date')))
        perf = {}
        for court_id, res_date in tmp:
            if not court_id:
                court_id = "Unknown"
            d = perf.setdefault(court_id, {"total": 0, "resolved": 0})
            d["total"] += 1
            if res_date:
                d["resolved"] += 1
        out = [{"court": k, "rate": (v["resolved"] / v["total"]) if v["total"] else 0.0} for k, v in perf.items()]
        # sort by rate desc
        out.sort(key=lambda x: x["rate"], reverse=True)
        return {"performance": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Court performance failed: {str(e)}")

# -------------------- Report Export --------------------
@app.post("/api/report/export-metrics")
async def export_metrics_to_report():
    """Insert latest model metrics into docs/PROJECT_REPORT.md placeholders."""
    try:
        comparison = ml_service.compare_models()
        # Build replacement lines
        lr = comparison.get('linear_regression', {})
        rf = comparison.get('random_forest', {})
        best = 'Random Forest' if (rf.get('r2_score', 0) or 0) >= (lr.get('r2_score', 0) or 0) else 'Linear Regression'

        base_dir = os.path.dirname(os.path.dirname(__file__))  # backend/
        project_root = os.path.abspath(os.path.join(base_dir, '..'))
        report_path = os.path.join(project_root, 'docs', 'PROJECT_REPORT.md')
        if not os.path.exists(report_path):
            raise HTTPException(status_code=404, detail="PROJECT_REPORT.md not found")
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        import re
        def fmt(model):
            return f"MAE: {model.get('mae', 0):.1f} days, R²: {model.get('r2_score', 0):.3f}, RMSE: {model.get('rmse', 0):.1f} days"

        content = re.sub(r"- Linear Regression — MAE: .*", f"- Linear Regression — {fmt(lr)}", content)
        content = re.sub(r"- Random Forest — MAE: .*", f"- Random Forest — {fmt(rf)}", content)
        content = re.sub(r"- Recommended model: .*", f"- Recommended model: {best}", content)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {"message": "Report updated", "report_path": report_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# -------------------- Feedback --------------------
@app.post("/api/feedback")
async def submit_feedback(payload: dict):
    """Store feedback in a JSONL file under uploads."""
    try:
        fb_dir = os.path.join(UPLOADS_ROOT, 'feedback')
        os.makedirs(fb_dir, exist_ok=True)
        fb_path = os.path.join(fb_dir, 'feedback.jsonl')
        payload = dict(payload)
        payload["timestamp"] = datetime.now().isoformat()
        with open(fb_path, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(payload) + "\n")
        return {"message": "Feedback received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback failed: {str(e)}")

@app.get("/api/analytics/predictions")
async def get_predictions(db: Session = Depends(get_db)):
    """Get ML predictions/metrics reflecting current trained model and data."""
    predictions = {
        "model_accuracy": 0.0,
        "predicted_avg_resolution": 0,
        "confidence_interval": [0, 0],
        "models_available": ["linear_regression", "random_forest"],
        "best_model": None,
    }
    # If trained, use model performance
    if getattr(ml_service, "is_trained", False):
        perf = getattr(ml_service, "model_performance", {}) or {}
        best = perf.get("random_forest", {}) if perf.get("random_forest", {}).get("r2_score", 0) >= perf.get("linear_regression", {}).get("r2_score", 0) else perf.get("linear_regression", {})
        predictions["model_accuracy"] = float(best.get("r2_score", 0))
        predictions["best_model"] = "random_forest" if best is perf.get("random_forest", {}) else "linear_regression"
        # crude CI from RMSE
        rmse = float(best.get("rmse", 0) or 0)
        # Estimate predicted average from current DB mean
        try:
            rows = db.query(Case.time_to_resolution_days).all()
            vals = [r[0] for r in rows if r[0] is not None]
            avg = int(sum(vals) / len(vals)) if vals else 0
        except Exception:
            avg = 0
        predictions["predicted_avg_resolution"] = avg
        predictions["confidence_interval"] = [max(avg - int(1.5 * rmse), 0), avg + int(1.5 * rmse)]
    return {"predictions": predictions}

@app.post("/api/analytics/train-models")
async def train_models():
    """Train both Linear Regression and Random Forest models"""
    try:
        # Load sample data for training
        df = pd.DataFrame(SAMPLE_CASES)
        result = ml_service.train_models(df)
        return {"training_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@app.post("/api/analytics/train-from-file")
async def train_from_file(file_path: str = Form(...), db: Session = Depends(get_db)):
    """Train models from a dataset file path (.csv or .xlsx) on the server."""
    try:
        df = ml_service.load_dataset(file_path)
        # Anonymize
        # Hash judge id regardless of column naming
        judge_cols = [c for c in df.columns if c.lower() in ['judge_id', 'judge', 'judge_id_hashed']]
        if judge_cols:
            col = judge_cols[0]
            df['judge_id_hashed'] = df[col].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest())
        # Persist minimal fields to DB
        try:
            for _, row in df.iterrows():
                case = Case(
                    case_id=str(row.get('case_id')),
                    court_id=str(row.get('court_id')),
                    location_region=str(row.get('location_region')),
                    case_type=str(row.get('case_type')),
                    filing_date=row.get('filing_date'),
                    resolution_date=row.get('resolution_date'),
                    num_hearings=int(row.get('num_hearings') or 0),
                    num_adjournments=int(row.get('num_adjournments') or 0),
                    judge_id_hashed=str(row.get('judge_id_hashed')),
                    outcome_category=str(row.get('outcome_category')) if row.get('outcome_category') is not None else None,
                    time_to_resolution_days=int(row.get('time_to_resolution_days')) if row.get('time_to_resolution_days') is not None else None,
                )
                # Upsert by case_id
                exists = db.query(Case).filter(Case.case_id == case.case_id).first()
                if exists:
                    for attr, val in case.__dict__.items():
                        if attr.startswith('_'): continue
                        setattr(exists, attr, val)
                else:
                    db.add(case)
            db.commit()
        except Exception:
            pass
        result = ml_service.train_models(df)
        return {"training_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training from file failed: {str(e)}")

@app.post("/api/analytics/upload-and-train")
async def upload_and_train(file: UploadFile = File(...)):
    """Upload a dataset (.csv or .xlsx) and train models immediately."""
    try:
        uploads_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        saved_path = os.path.join(uploads_dir, file.filename)

        with open(saved_path, "wb") as f:
            f.write(await file.read())

        df = ml_service.load_dataset(saved_path)
        # Keep a small preview for UI
        preview = df.head(5).fillna("").to_dict(orient='records')
        result = ml_service.train_models(df)
        return {"training_result": result, "saved_path": saved_path, "preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload/train failed: {str(e)}")

# -------------------- Files (PDF uploads) --------------------
@app.post("/api/files/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and store it on the server. Returns saved path and metadata."""
    try:
        filename = file.filename or "uploaded.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are allowed")

        uploads_dir = os.path.join(UPLOADS_ROOT, "pdfs")
        os.makedirs(uploads_dir, exist_ok=True)
        saved_path = os.path.join(uploads_dir, filename)

        with open(saved_path, "wb") as f:
            f.write(await file.read())

        public_url = f"/uploads/pdfs/{filename}"
        return {
            "message": "PDF uploaded successfully",
            "saved_path": saved_path,
            "filename": filename,
            "public_url": public_url,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")

def extract_cases_from_pdf(pdf_path: str) -> list[dict]:
    """Robust parser: tries PyPDF2, then pdfplumber, then OCR fallback (if available)."""
    # 1) PyPDF2 text
    try:
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        text = ""
    # 2) pdfplumber text if PyPDF2 failed/empty
    if not text.strip():
        try:
            with pdfplumber.open(pdf_path) as pdf:
                lines = []
                for page in pdf.pages:
                    lines.append(page.extract_text() or "")
                text = "\n".join(lines)
        except Exception:
            text = ""
    # 3) OCR fallback for scanned PDFs (optional)
    if not text.strip() and convert_from_path and pytesseract:
        try:
            pages = convert_from_path(pdf_path)
            ocr_text = []
            for img in pages[:3]:  # limit for performance
                ocr_text.append(pytesseract.image_to_string(img))
            text = "\n".join(ocr_text)
        except Exception:
            pass

    rows = []
    current = {}
    def commit():
        if current.get('case_id') and current.get('filing_date'):
            rows.append(current.copy())
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            # blank line separates cases
            if current:
                commit()
                current = {}
            continue
        if ':' in line:
            k, v = line.split(':', 1)
            key = k.strip().lower()
            val = v.strip()
            # map common keys
            key_map = {
                'case id': 'case_id',
                'case_id': 'case_id',
                'court id': 'court_id',
                'court_id': 'court_id',
                'region': 'location_region',
                'location_region': 'location_region',
                'type': 'case_type',
                'case type': 'case_type',
                'filing date': 'filing_date',
                'resolution date': 'resolution_date',
                'hearings': 'num_hearings',
                'num hearings': 'num_hearings',
                'adjournments': 'num_adjournments',
                'judge': 'judge_id_hashed',
                'outcome': 'outcome_category',
            }
            mapped = key_map.get(key)
            if mapped:
                current[mapped] = val
    if current:
        commit()
    return rows

@app.post("/api/analytics/upload-pdf-and-train")
async def upload_pdf_and_train(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a PDF, parse simple key:value lines into case rows, persist and train."""
    try:
        uploads_dir = os.path.join(UPLOADS_ROOT, "pdfs")
        os.makedirs(uploads_dir, exist_ok=True)
        saved_path = os.path.join(uploads_dir, file.filename)
        with open(saved_path, "wb") as f:
            f.write(await file.read())

        rows = extract_cases_from_pdf(saved_path)
        if not rows:
            return {"message": "No parsable cases found in PDF", "training_result": None}

        import pandas as pd
        df = pd.DataFrame(rows)
        # normalize and coerce types
        if 'judge_id_hashed' in df.columns:
            df['judge_id_hashed'] = df['judge_id_hashed'].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest())
        for col in ['num_hearings', 'num_adjournments']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        for dcol in ['filing_date', 'resolution_date']:
            if dcol in df.columns:
                df[dcol] = pd.to_datetime(df[dcol], errors='coerce').dt.date
        if 'time_to_resolution_days' not in df.columns and {'filing_date','resolution_date'}.issubset(df.columns):
            delta = pd.to_datetime(df['resolution_date']) - pd.to_datetime(df['filing_date'])
            df['time_to_resolution_days'] = (delta.dt.days).where(~delta.isna(), None)

        # persist
        for _, row in df.iterrows():
            case = Case(
                case_id=str(row.get('case_id')),
                court_id=str(row.get('court_id') or ''),
                location_region=str(row.get('location_region') or ''),
                case_type=str(row.get('case_type') or ''),
                filing_date=row.get('filing_date'),
                resolution_date=row.get('resolution_date'),
                num_hearings=int(row.get('num_hearings') or 0),
                num_adjournments=int(row.get('num_adjournments') or 0),
                judge_id_hashed=str(row.get('judge_id_hashed') or ''),
                outcome_category=str(row.get('outcome_category')) if row.get('outcome_category') is not None else None,
                time_to_resolution_days=int(row.get('time_to_resolution_days')) if row.get('time_to_resolution_days') is not None else None,
            )
            exists = db.query(Case).filter(Case.case_id == case.case_id).first()
            if exists:
                for attr, val in case.__dict__.items():
                    if attr.startswith('_'): continue
                    setattr(exists, attr, val)
            else:
                db.add(case)
        db.commit()

        preview = df.head(5).fillna("").to_dict(orient='records')
        result = ml_service.train_models(df)
        return {"message": "PDF parsed and trained", "rows": len(rows), "training_result": result, "preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload/parse/train failed: {str(e)}")

@app.post("/api/analytics/upload-data-and-train")
async def upload_data_and_train(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an Excel/CSV file, normalize columns, persist, and train models."""
    try:
        uploads_dir = os.path.join(UPLOADS_ROOT, "data")
        os.makedirs(uploads_dir, exist_ok=True)
        saved_path = os.path.join(uploads_dir, file.filename)
        with open(saved_path, "wb") as f:
            f.write(await file.read())

        # Reuse dataset loader to normalize columns/types
        df = ml_service.load_dataset(saved_path)

        # Hash judge id regardless of column naming
        judge_cols = [c for c in df.columns if c.lower() in ['judge_id', 'judge', 'judge_id_hashed']]
        if judge_cols:
            col = judge_cols[0]
            df['judge_id_hashed'] = df[col].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest())

        # Persist
        for _, row in df.iterrows():
            case = Case(
                case_id=str(row.get('case_id')),
                court_id=str(row.get('court_id') or ''),
                location_region=str(row.get('location_region') or ''),
                case_type=str(row.get('case_type') or ''),
                filing_date=row.get('filing_date'),
                resolution_date=row.get('resolution_date'),
                num_hearings=int(row.get('num_hearings') or 0),
                num_adjournments=int(row.get('num_adjournments') or 0),
                judge_id_hashed=str(row.get('judge_id_hashed') or ''),
                outcome_category=str(row.get('outcome_category')) if row.get('outcome_category') is not None else None,
                time_to_resolution_days=int(row.get('time_to_resolution_days')) if row.get('time_to_resolution_days') is not None else None,
            )
            existing = db.query(Case).filter(Case.case_id == case.case_id).first()
            if existing:
                for attr, val in case.__dict__.items():
                    if attr.startswith('_'): continue
                    setattr(existing, attr, val)
            else:
                db.add(case)
        db.commit()

        preview = df.head(5).fillna("").to_dict(orient='records')
        result = ml_service.train_models(df)
        return {"message": "Data uploaded and trained", "saved_path": saved_path, "training_result": result, "preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload/train failed: {str(e)}")

@app.get("/api/analytics/model-comparison")
async def get_model_comparison():
    """Get comparison between Linear Regression and Random Forest models"""
    try:
        comparison = ml_service.compare_models()
        return {"comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.post("/api/analytics/predict")
async def predict_case_resolution(case_data: dict):
    """Predict resolution time for a new case"""
    try:
        prediction = ml_service.predict_resolution_time(case_data)
        return {"prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/api/analytics/model-insights")
async def get_model_insights():
    """Get detailed insights from trained models"""
    try:
        insights = ml_service.get_model_insights()
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights failed: {str(e)}")

@app.get("/api/analytics/model-comparison-report")
async def get_model_comparison_report():
    """Return MAE/R²/RMSE metrics for report insertion."""
    try:
        comparison = ml_service.compare_models()
        return {"comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report metrics failed: {str(e)}")

@app.get("/api/courts")
async def get_courts():
    """Get list of courts"""
    courts = [
        {"court_id": "HC-001", "name": "High Court Kampala", "region": "Central"},
        {"court_id": "MC-001", "name": "Magistrate Court Jinja", "region": "Eastern"},
        {"court_id": "MC-002", "name": "Magistrate Court Gulu", "region": "Northern"}
    ]
    return {"courts": courts}

# Serve React app for any non-API routes (SPA routing)
# This must be last to catch all non-API routes
@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve React app for client-side routing"""
    # Don't serve SPA for API, uploads, or static paths
    if path.startswith(("api/", "uploads/", "static/")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if requesting a specific static file
    static_file = os.path.join(STATIC_ROOT, path) if os.path.exists(STATIC_ROOT) else None
    if static_file and os.path.exists(static_file) and os.path.isfile(static_file):
        return FileResponse(static_file)
    
    # Serve index.html (React Router will handle client-side routing)
    index_path = os.path.join(STATIC_ROOT, "index.html") if os.path.exists(STATIC_ROOT) else None
    if index_path and os.path.exists(index_path):
        return FileResponse(index_path)
    
    # If no static files directory, return 404
    raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8010"))
    uvicorn.run(app, host=host, port=port)
