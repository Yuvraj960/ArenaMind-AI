/**
 * ArenaMind API client — calls the backend FastAPI gateway.
 * Falls back gracefully when the backend is not running (offline dev mode).
 */

import type {
  ChatRequest,
  ChatResponse,
  GateDensity,
  HeatmapPoint,
  NavigationRoute,
  EmergencyResponse,
  OperationsResponse,
} from "./types";

const API_BASE =
  typeof window !== "undefined"
    ? `/api/v1`
    : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1`;

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`chat failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

export interface NavigationPayload {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  accessibility_needs: string[];
  avoid_crowds: boolean;
}

export interface NavigationResponse {
  primary_route: NavigationRoute;
  alternatives: NavigationRoute[];
  crowd_warnings: { gate_id: string; message: string }[];
  accessibility_notes: string[];
  estimated_arrival: string;
}

export async function getRoute(payload: NavigationPayload): Promise<NavigationResponse> {
  const res = await fetch(`${API_BASE}/navigation/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`navigation failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Crowd
// ---------------------------------------------------------------------------

export async function getGateDensities(): Promise<GateDensity[]> {
  const res = await fetch(`${API_BASE}/crowd/gates`);
  if (!res.ok) throw new Error(`crowd/gates failed: ${res.status}`);
  return res.json();
}

export async function getHeatmap(): Promise<{
  success: boolean;
  heatmap: HeatmapPoint[];
  gates: GateDensity[];
  narrative: string;
}> {
  const res = await fetch(`${API_BASE}/crowd/heatmap`);
  if (!res.ok) throw new Error(`crowd/heatmap failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Operations
// ---------------------------------------------------------------------------

export async function operationsQuery(question: string): Promise<OperationsResponse> {
  const res = await fetch(`${API_BASE}/operations/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`operations query failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Emergency
// ---------------------------------------------------------------------------

export interface EmergencyScenario {
  type: "medical" | "fire" | "security" | "evacuation";
  location: { lat: number; lng: number };
  severity: "low" | "medium" | "high" | "critical";
  details: string;
  reported_by: string;
}

export async function emergencyRespond(
  scenario: EmergencyScenario
): Promise<EmergencyResponse> {
  const res = await fetch(`${API_BASE}/emergency/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenario),
  });
  if (!res.ok) throw new Error(`emergency/respond failed: ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Stadium / Simulator
// ---------------------------------------------------------------------------

export async function triggerSimEvent(
  eventType: string,
  affectsGate: string,
  multiplier: number
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/stadium/simulate/event?event_type=${eventType}&gate_id=${affectsGate}&multiplier=${multiplier}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`simulate/event failed: ${res.status}`);
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

export async function healthCheck(): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/`);
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return res.json();
}