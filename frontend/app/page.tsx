import Link from "next/link";

const ROLES = [
  {
    id: "fan",
    label: "Fan",
    emoji: "🎟️",
    description: "Matchday assistant — ask anything, get navigation, find amenities.",
    href: "/fan",
    accent: "border-blue-400 hover:border-blue-600 hover:bg-blue-50",
    icon: "text-blue-600",
  },
  {
    id: "ops",
    label: "Operations",
    emoji: "🛡️",
    description: "Crowd intelligence dashboard, ops copilot, gate & transit monitoring.",
    href: "/ops/dashboard",
    accent: "border-amber-400 hover:border-amber-600 hover:bg-amber-50",
    icon: "text-amber-600",
  },
  {
    id: "volunteer",
    label: "Volunteer",
    emoji: "🦸",
    description: "SOP lookup, accessibility routing, lost-child protocols — all offline-first.",
    href: "/volunteer",
    accent: "border-emerald-400 hover:border-emerald-600 hover:bg-emerald-50",
    icon: "text-emerald-600",
  },
  {
    id: "emergency",
    label: "Emergency",
    emoji: "🚨",
    description: "Real-time emergency response plan generator, exits, medical, announcements.",
    href: "/emergency",
    accent: "border-red-400 hover:border-red-600 hover:bg-red-50",
    icon: "text-red-600",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-arena-900 text-white py-6 px-8 shadow-lg">
        <div className="max-w-6xl mx-auto flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-arena-500 flex items-center justify-center text-xl font-bold">
            ⚡
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">ArenaMind AI</h1>
            <p className="text-arena-300 text-sm">
              FIFA World Cup 2026 — Generative AI Stadium Operating System
            </p>
          </div>
          <div className="ml-auto text-right hidden sm:block">
            <span className="text-xs text-arena-400">Powered by Claude + Stadium Simulator</span>
            <br />
            <span className="text-xs text-arena-500">Demo environment — no live CCTV</span>
          </div>
        </div>
      </header>

      {/* Hero + role selection */}
      <section className="flex-1 py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-sm font-semibold text-arena-600 uppercase tracking-widest mb-2">
              FIFA World Cup 2026 — Demo Mode
            </p>
            <h2 className="text-4xl font-extrabold text-slate-900 mb-4">
              Choose your role
            </h2>
            <p className="text-slate-500 text-lg max-w-2xl mx-auto">
              Four dedicated interfaces for the four ArenaMind stakeholders. Each panel runs
              fully offline with simulated crowd data — upgrade to live services in one click.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {ROLES.map((role) => (
              <Link
                key={role.id}
                href={role.href}
                className={`group block border-2 rounded-2xl p-6 bg-white shadow-sm transition-all duration-200 hover:shadow-md ${role.accent}`}
              >
                <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">
                  {role.emoji}
                </div>
                <h3 className={`text-xl font-bold mb-1 ${role.icon}`}>{role.label}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">
                  {role.description}
                </p>
                <div className="mt-4 flex items-center gap-1 text-sm font-semibold text-slate-400 group-hover:text-slate-700 transition-colors">
                  Open {role.label} →
                </div>
              </Link>
            ))}
          </div>

          {/* Demo beats callout */}
          <div className="mt-16 bg-arena-900 rounded-2xl p-8 text-white">
            <h3 className="text-lg font-bold mb-4">Demo acceptance criteria</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
              {[
                ["🇪🇸", "Spanish fan navigation", "Route around Gate B (85% full) to Gate C"],
                ["📊", "Crowd surge alert", "Gate B rises to critical → routes fan away"],
                ["🚑", "Medical emergency", "Evacuate exits + medical + EN/ES announcements"],
                ["🌧️", "Rain-driven transit", "Metro Line 2 delay → crowd shift"],
                ["🏁", "Post-match summary", "GenAI crowd narrative after match"],
              ].map(([emoji, title, desc]) => (
                <div key={title as string} className="flex gap-3">
                  <span className="text-xl">{emoji as string}</span>
                  <div>
                    <div className="font-semibold">{title as string}</div>
                    <div className="text-arena-300 text-xs mt-0.5">{desc as string}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <footer className="bg-slate-900 text-slate-500 text-xs text-center py-4">
        ArenaMind AI — FIFA WC 2026 Demo. Simulated data only. No live CCTV or real-time camera feeds.
      </footer>
    </main>
  );
}