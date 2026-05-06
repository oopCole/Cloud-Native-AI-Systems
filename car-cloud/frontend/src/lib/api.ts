export type Car = {
  id: number;
  make: string;
  model: string;
  year: number;
  price_usd: number;
  mpg: number | null;
};

export type CarCreate = {
  make: string;
  model: string;
  year: number;
  price_usd: number;
  mpg: number | null;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/car-api";

export async function fetchCars(): Promise<Car[]> {
  const res = await fetch(`${API_BASE}/api/cars`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch cars (${res.status})`);
  }
  return (await res.json()) as Car[];
}

export async function createCar(payload: CarCreate): Promise<Car> {
  const res = await fetch(`${API_BASE}/api/cars`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to create car (${res.status})`);
  }
  return (await res.json()) as Car;
}

export type VehicleQuery = {
  vin?: string;
  make?: string;
  model?: string;
  year?: number;
};

export type RecallItem = {
  nhtsa_id: string;
  component: string;
  summary: string;
  consequence: string;
  remedy: string;
  severity: string;
};

export type FailureBucket = {
  mileage_range: string;
  issue: string;
  mentions: number;
};

export type RiskScoreResult = {
  score: number;
  level: string;
  rationale: string;
};

export type AnalyzeVehicleResult = {
  input: Record<string, unknown>;
  resolved_vehicle: Record<string, unknown>;
  risk_score: RiskScoreResult;
  recalls: RecallItem[];
  common_failures: FailureBucket[];
  ai_summary: string;
};

export async function analyzeVehicle(
  payload: VehicleQuery,
): Promise<AnalyzeVehicleResult> {
  const res = await fetch(`${API_BASE}/analyze-vehicle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Failed to analyze vehicle (${res.status})`);
  }
  return (await res.json()) as AnalyzeVehicleResult;
}
