// Shared TypeScript types for the ArenaMind frontend

export type Role = "fan" | "operator" | "volunteer" | "emergency";
export type Language = "en" | "es" | "fr" | "ar";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_used?: string;
  sources?: string[];
  suggested_actions?: string[];
  language?: Language;
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  language: Language;
  role: Role;
  session_id: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  agent_used: string;
  session_id: string;
  sources: string[];
  suggested_actions: string[];
  language: Language;
}

export interface GateDensity {
  gate_id: string;
  gate_name: string;
  current_count: number;
  capacity: number;
  density_percentage: number;
  trend: "increasing" | "stable" | "decreasing";
  estimated_wait_minutes: number;
  status: string;
  accessibility_features: string[];
}

export interface HeatmapPoint {
  lat: number;
  lng: number;
  intensity: number;
  count: number;
  type: string;
  gate_id?: string;
  section_id?: string;
}

export interface NavigationRoute {
  id: string;
  origin: { lat: number; lng: number; label?: string };
  destination: { lat: number; lng: number; label?: string };
  waypoints: { location: { lat: number; lng: number; label: string }; instruction: string }[];
  total_distance_m: number;
  total_time_sec: number;
  reasoning: string;
}

export interface EmergencyResponse {
  success: boolean;
  scenario_id: string;
  nearest_exits: { gate_id: string; name: string; distance_m: number }[];
  nearest_medical: { name: string; distance_m: number }[];
  nearest_security: { name: string; distance_m: number }[];
  announcements: { language: string; text: string }[];
  immediate_actions: string[];
  evacuation_routes: string[];
  estimated_clearance_time_min: number;
  coordination_notes: string;
}

export interface OperationsResponse {
  success: boolean;
  answer: string;
  data_sources: string[];
  confidence: number;
  recommended_actions: string[];
  related_metrics: Record<string, number>;
}