from __future__ import annotations

from collections import Counter
from typing import Any, List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    FRONTEND_ORIGIN,
)


class Car(BaseModel):
    id: int
    make: str
    model: str
    year: int = Field(ge=1886, le=2100)
    price_usd: int = Field(ge=0)
    mpg: float | None = Field(default=None, ge=0)


class CarCreate(BaseModel):
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    year: int = Field(ge=1886, le=2100)
    price_usd: int = Field(ge=0)
    mpg: float | None = Field(default=None, ge=0)


app = FastAPI(title="car-cloud-backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Starter in-memory data store for a base prototype.
cars: List[Car] = [
    Car(id=1, make="Toyota", model="Camry", year=2023, price_usd=29000, mpg=32),
    Car(id=2, make="Honda", model="Civic", year=2024, price_usd=27000, mpg=35),
    Car(id=3, make="Tesla", model="Model 3", year=2024, price_usd=39990, mpg=None),
]
next_id = 4


class VehicleQuery(BaseModel):
    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1886, le=2100)


class RecallItem(BaseModel):
    nhtsa_id: str
    component: str
    summary: str
    consequence: str
    remedy: str
    severity: str


class FailureBucket(BaseModel):
    mileage_range: str
    issue: str
    mentions: int


class RiskScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)
    level: str
    rationale: str


class AnalyzeVehicleResult(BaseModel):
    input: dict[str, Any]
    resolved_vehicle: dict[str, Any]
    risk_score: RiskScoreResult
    recalls: list[RecallItem]
    common_failures: list[FailureBucket]
    ai_summary: str


SEVERITY_KEYWORDS = {
    "critical": ["fire", "crash", "injury", "death", "air bag", "airbag", "brake"],
    "high": ["stall", "steer", "fuel leak", "battery"],
    "medium": ["electrical", "camera", "display", "sensor"],
}

MILEAGE_BUCKETS = [
    "0-30k",
    "30k-60k",
    "60k-100k",
    "100k+",
]


def _normalize_vehicle_query(query: VehicleQuery) -> dict[str, Any]:
    vin = (query.vin or "").strip().upper()
    make = (query.make or "").strip()
    model = (query.model or "").strip()
    year = query.year
    if vin:
        return {"vin": vin, "make": make, "model": model, "year": year}
    if not (make and model and year):
        raise HTTPException(
            status_code=422,
            detail="Provide VIN or (make, model, year).",
        )
    return {"vin": "", "make": make, "model": model, "year": year}


def _severity_from_text(text: str) -> str:
    lowered = text.lower()
    for label, keys in SEVERITY_KEYWORDS.items():
        if any(k in lowered for k in keys):
            return label
    return "low"


def _recall_to_failure_issue(recall: RecallItem) -> str:
    text = f"{recall.component} {recall.summary}".lower()
    if "brake" in text:
        return "Brake system concerns"
    if "air bag" in text or "airbag" in text:
        return "Airbag/SRS safety issues"
    if "electrical" in text or "battery" in text:
        return "Electrical system reliability"
    if "steer" in text:
        return "Steering control issues"
    if "fuel" in text:
        return "Fuel system concerns"
    return "General safety-related defect"


def _mileage_bucket_for_issue(issue: str) -> str:
    issue_lower = issue.lower()
    if "electrical" in issue_lower or "airbag" in issue_lower:
        return "30k-60k"
    if "brake" in issue_lower or "steering" in issue_lower:
        return "60k-100k"
    if "fuel" in issue_lower:
        return "100k+"
    return "0-30k"


def _build_common_failures(recalls: list[RecallItem]) -> list[FailureBucket]:
    if not recalls:
        return []
    counts: Counter[tuple[str, str]] = Counter()
    for recall in recalls:
        issue = _recall_to_failure_issue(recall)
        bucket = _mileage_bucket_for_issue(issue)
        counts[(bucket, issue)] += 1
    items: list[FailureBucket] = []
    for (bucket, issue), mentions in counts.most_common(5):
        items.append(FailureBucket(mileage_range=bucket, issue=issue, mentions=mentions))
    return items


def _risk_level(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _build_risk_score(recalls: list[RecallItem]) -> RiskScoreResult:
    if not recalls:
        return RiskScoreResult(
            score=15,
            level="low",
            rationale="No active recalls found from current data sources.",
        )

    severity_weights = {"critical": 18, "high": 12, "medium": 7, "low": 4}
    score = min(100, sum(severity_weights.get(r.severity, 4) for r in recalls))
    level = _risk_level(score)
    rationale = (
        f"Computed from {len(recalls)} recall records with severity weighting "
        f"(critical/high/medium/low)."
    )
    return RiskScoreResult(score=score, level=level, rationale=rationale)


def _fallback_summary(
    vehicle: dict[str, Any],
    risk_score: RiskScoreResult,
    recalls: list[RecallItem],
    failures: list[FailureBucket],
) -> str:
    vehicle_name = (
        f"{vehicle.get('year', 'Unknown')} {vehicle.get('make', '')} {vehicle.get('model', '')}"
    ).strip()
    top_failure = failures[0].issue if failures else "No dominant issue pattern found"
    return (
        f"{vehicle_name}: Risk level is {risk_score.level.upper()} ({risk_score.score}/100). "
        f"Detected {len(recalls)} recall entries. "
        f"Most common failure theme: {top_failure}. "
        "Review recall remedy actions and service history before purchase or long trips."
    )


async def _generate_ai_summary(
    vehicle: dict[str, Any],
    risk_score: RiskScoreResult,
    recalls: list[RecallItem],
    failures: list[FailureBucket],
) -> str:
    fallback = _fallback_summary(vehicle, risk_score, recalls, failures)
    if not AI_API_KEY:
        return fallback

    recall_lines = [
        f"- [{r.severity}] {r.component}: {r.summary[:180]}" for r in recalls[:6]
    ]
    failure_lines = [
        f"- {f.mileage_range}: {f.issue} ({f.mentions} mentions)" for f in failures[:5]
    ]

    prompt = (
        "You are a vehicle reliability assistant. "
        "Write a concise vehicle health summary (4-6 bullet points) with no markdown header.\n\n"
        f"Vehicle: {vehicle}\n"
        f"Risk score: {risk_score.score} ({risk_score.level})\n"
        "Recall findings:\n"
        + ("\n".join(recall_lines) if recall_lines else "- none")
        + "\nCommon failures by mileage:\n"
        + ("\n".join(failure_lines) if failure_lines else "- none")
    )

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{AI_BASE_URL.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": AI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return content or fallback
    except Exception:
        return fallback


async def _resolve_vehicle(vin: str, make: str, model: str, year: int | None) -> dict[str, Any]:
    if not vin:
        return {"vin": "", "make": make, "model": model, "year": year}
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    data = resp.json().get("Results", [{}])[0]
    return {
        "vin": vin,
        "make": data.get("Make") or make,
        "model": data.get("Model") or model,
        "year": int(data["ModelYear"]) if str(data.get("ModelYear", "")).isdigit() else year,
    }


async def _fetch_vehicle_recalls(make: str, model: str, year: int) -> list[RecallItem]:
    url = "https://api.nhtsa.gov/recalls/recallsByVehicle"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            url,
            params={"make": make, "model": model, "modelYear": year},
        )
        resp.raise_for_status()
    rows = resp.json().get("results", [])
    recalls: list[RecallItem] = []
    for row in rows:
        text = f"{row.get('Summary', '')} {row.get('Consequence', '')}"
        recalls.append(
            RecallItem(
                nhtsa_id=row.get("NHTSACampaignNumber", ""),
                component=row.get("Component", "Unknown"),
                summary=row.get("Summary", ""),
                consequence=row.get("Consequence", ""),
                remedy=row.get("Remedy", ""),
                severity=_severity_from_text(text),
            )
        )
    return recalls


async def _analyze(query: VehicleQuery) -> AnalyzeVehicleResult:
    normalized = _normalize_vehicle_query(query)
    resolved = await _resolve_vehicle(
        vin=normalized["vin"],
        make=normalized["make"],
        model=normalized["model"],
        year=normalized["year"],
    )
    make = (resolved.get("make") or "").strip()
    model = (resolved.get("model") or "").strip()
    year = resolved.get("year")
    if not (make and model and isinstance(year, int)):
        raise HTTPException(
            status_code=400,
            detail="Could not resolve vehicle details. Provide make/model/year explicitly.",
        )
    recalls = await _fetch_vehicle_recalls(make, model, year)
    risk_score = _build_risk_score(recalls)
    failures = _build_common_failures(recalls)
    ai_summary = await _generate_ai_summary(resolved, risk_score, recalls, failures)
    return AnalyzeVehicleResult(
        input=normalized,
        resolved_vehicle=resolved,
        risk_score=risk_score,
        recalls=recalls,
        common_failures=failures,
        ai_summary=ai_summary,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/cars", response_model=List[Car])
def list_cars() -> List[Car]:
    return cars


@app.get("/api/cars/{car_id}", response_model=Car)
def get_car(car_id: int) -> Car:
    for car in cars:
        if car.id == car_id:
            return car
    raise HTTPException(status_code=404, detail="Car not found")


@app.post("/api/cars", response_model=Car, status_code=201)
def create_car(payload: CarCreate) -> Car:
    global next_id
    car = Car(id=next_id, **payload.model_dump())
    cars.append(car)
    next_id += 1
    return car


@app.post("/vehicle-recalls", response_model=list[RecallItem])
async def vehicle_recalls(query: VehicleQuery) -> list[RecallItem]:
    result = await _analyze(query)
    return result.recalls


@app.post("/risk-score", response_model=RiskScoreResult)
async def risk_score(query: VehicleQuery) -> RiskScoreResult:
    result = await _analyze(query)
    return result.risk_score


@app.post("/common-failures", response_model=list[FailureBucket])
async def common_failures(query: VehicleQuery) -> list[FailureBucket]:
    result = await _analyze(query)
    return result.common_failures


@app.post("/ai-summary")
async def ai_summary(query: VehicleQuery) -> dict[str, str]:
    result = await _analyze(query)
    return {"summary": result.ai_summary}


@app.post("/analyze-vehicle", response_model=AnalyzeVehicleResult)
async def analyze_vehicle(query: VehicleQuery) -> AnalyzeVehicleResult:
    return await _analyze(query)
