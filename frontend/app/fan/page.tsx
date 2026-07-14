import type { Metadata } from "next";
import Link from "next/link";
import ChatWidget from "@/components/ChatWidget";

export const metadata: Metadata = { title: "ArenaMind — Fan Chat" };

export default function FanPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top bar */}
      <header className="bg-arena-900 text-white px-6 py-4 flex items-center gap-4 shadow">
        <Link href="/" className="text-arena-300 hover:text-white text-sm flex items-center gap-1">
          ← Home
        </Link>
        <div className="w-px h-5 bg-arena-600" />
        <span className="text-xl font-bold">🎟️ Fan — Matchday Assistant</span>
        <span className="ml-auto text-xs text-arena-400 hidden sm:block">
          RAG-backed · Multilingual · Accessible routing
        </span>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 max-w-7xl mx-auto w-full">
        {/* Chat */}
        <div className="flex-1 min-h-[600px]">
          <ChatWidget
            sessionId="fan-matchday"
            role="fan"
            language="en"
            placeholder="Ask about gates, navigation, food, policies..."
            welcomeMessage={
              "🎟️ Welcome to ArenaMind Matchday Assistant!\n\n" +
              "I can help you find your gate, navigate the stadium, answer questions about amenities, and more.\n\n" +
              "Try asking in English or Spanish — e.g. '¿Dónde está la Gate A?'"
            }
          />
        </div>

        {/* Side panel */}
        <aside className="lg:w-72 flex-shrink-0 space-y-3">
          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <h3 className="font-semibold text-slate-700 text-sm mb-3">💬 Try these prompts</h3>
            <div className="space-y-2 text-xs">
              {[
                { lang: "EN", text: "Where is the accessible entrance?" },
                { lang: "ES", text: "¿Dónde está la Gate A?" },
                { lang: "EN", text: "I'm at the south metro, how do I get to my gate?" },
                { lang: "ES", text: "¿Hay alerta de lluvia?" },
                { lang: "EN", text: "Lost my tickets near section 204" },
                { lang: "EN", text: "Nearest food court with vegan options" },
              ].map((s, i) => (
                <div key={i} className="px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-600">
                  <span className="font-bold text-arena-500 text-[10px] mr-1">{s.lang}</span>
                  {s.text}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-arena-50 rounded-2xl border border-arena-200 p-4">
            <h4 className="font-semibold text-arena-800 text-xs mb-2">👁️ Demo beat</h4>
            <p className="text-xs text-arena-700">
              Gate B is at 85% capacity — ask in Spanish to see dynamic crowd-aware routing redirect you to Gate C.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm">
            <h4 className="font-semibold text-slate-700 text-xs mb-2">📍 Gate live densities</h4>
            <div className="space-y-1 text-xs text-slate-600">
              {[
                { name: "Gate A — North", pct: 25, badge: "~25%" },
                { name: "Gate B — East ⚠️", pct: 85, badge: "85%", warn: true },
                { name: "Gate C — South", pct: 20, badge: "~20%" },
                { name: "Gate D — West", pct: 20, badge: "~20%" },
              ].map((g) => (
                <div key={g.name} className="flex justify-between items-center py-1 border-b border-slate-100 last:border-0">
                  <span className={g.warn ? "text-red-600 font-semibold" : ""}>{g.name}</span>
                  <span className={g.warn ? "text-red-600 font-bold" : "text-slate-400"}>{g.badge}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}