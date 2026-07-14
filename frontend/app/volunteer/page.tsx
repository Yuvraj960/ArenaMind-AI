import type { Metadata } from "next";
import ChatWidget from "@/components/ChatWidget";
import Link from "next/link";

export const metadata: Metadata = { title: "ArenaMind — Volunteer Copilot" };

export default function VolunteerPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-emerald-700 text-white px-6 py-4 flex items-center gap-4 shadow">
        <Link href="/" className="text-emerald-200 hover:text-white text-sm">← Home</Link>
        <div className="w-px h-5 bg-emerald-500" />
        <span className="text-xl font-bold">🦸 Volunteer Copilot</span>
        <span className="ml-auto text-xs text-emerald-300 hidden sm:block">
          RAG-backed SOP access — offline-first
        </span>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-7xl mx-auto w-full">
        <div className="flex-1 min-h-[600px]">
          <ChatWidget
            sessionId="volunteer-copilot"
            role="volunteer"
            language="en"
            placeholder="Search SOPs, protocols, accessibility guides..."
            welcomeMessage={
              "🦸 Volunteer Copilot — your field guide is here.\n\n" +
              "Ask me about:\n" +
              "• Lost children procedures\n" +
              "• Accessibility routing for wheelchairs\n" +
              "• Medical escalation protocols\n" +
              "• Gate management and crowd control\n" +
              "• Stadium-specific SOPs"
            }
          />
        </div>

        <aside className="lg:w-72 flex-shrink-0 space-y-3">
          <div className="bg-emerald-50 rounded-2xl border border-emerald-200 p-4">
            <h4 className="font-semibold text-emerald-800 text-xs mb-2">📋 Quick SOP refs</h4>
            <ul className="space-y-1.5 text-xs text-emerald-700">
              {[
                "Lost children → reunite at Info Desk",
                "Medical → call 111, clear area",
                "Evacuation → Gate A, C, F exits",
                "VIP escalation → radio control",
              ].map((tip) => (
                <li key={tip} className="flex gap-1.5">
                  <span className="text-emerald-400 mt-0.5">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <h4 className="font-semibold text-slate-700 text-xs mb-2">🔑 Accessibility routing</h4>
            <p className="text-xs text-slate-500">
              All navigation requests automatically consider wheelchair/low-mobility needs. Routes prefer Gates A, C, and F which have full accessibility features.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <h4 className="font-semibold text-slate-700 text-xs mb-2">🚪 Accessible gates</h4>
            <div className="space-y-1 text-xs text-slate-600">
              {[
                { gate: "Gate A", features: "wheelchair, express, assistance" },
                { gate: "Gate C", features: "wheelchair, express" },
                { gate: "Gate F", features: "wheelchair, priority, assistance" },
              ].map((g) => (
                <div key={g.gate} className="py-1 border-b border-slate-100 last:border-0">
                  <div className="font-semibold">{g.gate}</div>
                  <div className="text-slate-400">{g.features}</div>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}