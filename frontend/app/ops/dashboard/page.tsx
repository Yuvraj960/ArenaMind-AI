"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getGateDensities, getHeatmap, triggerSimEvent } from "@/lib/api";
import type { GateDensity, HeatmapPoint } from "@/lib/types";

function GateBar({ gate }: { gate: GateDensity }) {
  const pct = Math.min(gate.density_percentage, 100);
  const color =
    pct >= 80 ? "bg-red-500" : pct >= 60 ? "bg-amber-500" : pct >= 40 ? "bg-yellow-500" : "bg-emerald-500";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-semibold text-slate-800 text-sm">{gate.gate_name}</div>
          <div className="text-xs text-slate-400">{gate.gate_id}</div>
        </div>
        <div className="text-right">
          <div className={`font-bold text-sm ${pct >= 80 ? "text-red-600" : "text-slate-600"}`}>
            {pct.toFixed(0)}%
          </div>
          <div className="text-xs text-slate-400">{gate.current_count}/{gate.capacity}</div>
        </div>
      </div>
      {/* Density bar */}
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between items-center mt-2">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          gate.trend === "increasing" ? "bg-red-100 text-red-600" :
          gate.trend === "decreasing" ? "bg-emerald-100 text-emerald-600" :
          "bg-slate-100 text-slate-500"
        }`}>
          {gate.trend}
        </span>
        {gate.estimated_wait_minutes > 0 && (
          <span className="text-xs text-slate-400">{gate.estimated_wait_minutes}min wait</span>
        )}
      </div>
      {gate.accessibility_features.length > 0 && (
        <div className="flex gap-1 mt-1.5">
          {gate.accessibility_features.map((f) => (
            <span key={f} className="text-[10px] px-1.5 py-0.5 rounded bg-arena-50 text-arena-600">
              ♿ {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function OpsDashboard() {
  const [gates, setGates] = useState<GateDensity[]>([]);
  const [narrative, setNarrative] = useState("");
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  async function load() {
    try {
      const [gateData, heatmapData] = await Promise.all([getGateDensities(), getHeatmap()]);
      setGates(gateData);
      setNarrative(heatmapData.narrative || "");
    } catch {
      // Backend offline — show empty state
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSurge() {
    setTriggering(true);
    try {
      await triggerSimEvent("surge", "gate_b", 3.0);
      await load();
    } finally {
      setTriggering(false);
    }
  }

  const avgDensity = gates.length > 0
    ? (gates.reduce((s, g) => s + g.density_percentage, 0) / gates.length).toFixed(0)
    : "0";

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-arena-900 text-white px-6 py-4 flex items-center gap-4 shadow">
        <Link href="/" className="text-arena-300 hover:text-white text-sm">← Home</Link>
        <div className="w-px h-5 bg-arena-600" />
        <span className="text-xl font-bold">🛡️ Operations Copilot</span>
        <span className="ml-auto text-xs text-arena-400 hidden sm:block">Crowd intelligence dashboard</span>
      </header>

      <div className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* KPI row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Avg crowd density", value: `${avgDensity}%`, emoji: "📊" },
            { label: "Gates at risk", value: `${gates.filter(g => g.density_percentage >= 80).length}/6`, emoji: "🚨" },
            { label: "Increasing trend", value: `${gates.filter(g => g.trend === "increasing").length}`, emoji: "📈" },
          ].map((kpi) => (
            <div key={kpi.label} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex items-center gap-4">
              <span className="text-2xl">{kpi.emoji}</span>
              <div>
                <div className="text-2xl font-bold text-slate-800">{kpi.value}</div>
                <div className="text-xs text-slate-500">{kpi.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* GenAI narrative */}
        {narrative && (
          <div className="bg-arena-900 text-white rounded-2xl p-6 shadow-lg">
            <h3 className="text-xs font-semibold text-arena-300 uppercase tracking-widest mb-2">
              AI crowd narrative
            </h3>
            <p className="text-sm leading-relaxed text-arena-100">{narrative}</p>
          </div>
        )}

        {/* Gate grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-800">Gate densities</h2>
            <button
              onClick={handleSurge}
              disabled={triggering}
              className="px-4 py-2 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {triggering ? "Triggering surge..." : "🔥 Trigger surge at Gate B"}
            </button>
          </div>

          {loading ? (
            <div className="flex gap-4 overflow-x-auto pb-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex-shrink-0 w-48 h-32 bg-slate-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              {gates.map((gate) => (
                <GateBar key={gate.gate_id} gate={gate} />
              ))}
            </div>
          )}
        </div>

        {/* Operations chat */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">🧠 Operations Copilot — Query</h3>
          <p className="text-xs text-slate-400 mb-3">Backend is offline (run `uvicorn app.main:app` to connect)</p>
        </div>
      </div>
    </div>
  );
}