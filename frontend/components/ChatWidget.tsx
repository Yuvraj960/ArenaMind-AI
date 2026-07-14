"use client";

import { useState, useRef, useEffect } from "react";
import { SendIcon, BotIcon, UserIcon, InfoIcon, LoaderIcon } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { chat } from "@/lib/api";

interface ChatWidgetProps {
  sessionId?: string;
  role?: "fan" | "operator" | "volunteer" | "emergency";
  language?: "en" | "es" | "fr" | "ar";
  placeholder?: string;
  welcomeMessage?: string;
  className?: string;
}

const AGENT_LABELS: Record<string, string> = {
  knowledge: "Matchday Assistant",
  knowledge_volunteer: "Volunteer Copilot",
  navigation: "Navigation Agent",
  operations: "Operations Copilot",
  emergency: "Emergency AI",
  crowd: "Crowd Intelligence",
  translation: "Translation",
};

function formatText(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n\n/g, "<br/><br/>")
    .replace(/\n/g, "<br/>");
}

export default function ChatWidget({
  sessionId = `session-${Date.now()}`,
  role = "fan",
  language = "en",
  placeholder = "Ask me anything about the stadium...",
  welcomeMessage = "Hello! I'm your ArenaMind assistant. Ask me about gates, navigation, amenities, or anything matchday-related!",
  className = "",
}: ChatWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: welcomeMessage,
      agent_used: "knowledge",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      language,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await chat({
        message: text,
        language,
        role,
        session_id: sessionId,
      });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response,
        agent_used: data.agent_used,
        sources: data.sources,
        suggested_actions: data.suggested_actions,
        language: data.language,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            "I'm having trouble connecting to the ArenaMind gateway right now. Please try again in a moment. (backend may be offline)",
          agent_used: "system",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className={`flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden ${className}`}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            {/* Avatar */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs
              ${msg.role === "user"
                ? "bg-blue-500 text-white"
                : msg.agent_used === "emergency"
                ? "bg-red-500 text-white"
                : msg.agent_used === "navigation"
                ? "bg-arena-500 text-white"
                : "bg-slate-200 text-slate-700"
              }`}
            >
              {msg.role === "user" ? <UserIcon size={14} /> : <BotIcon size={14} />}
            </div>

            {/* Bubble */}
            <div className={`max-w-[80%] ${msg.role === "user" ? "text-right" : ""}`}>
              {msg.agent_used && msg.role === "assistant" && (
                <div className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1">
                  <BotIcon size={10} />
                  {AGENT_LABELS[msg.agent_used] ?? msg.agent_used}
                  {msg.language && msg.language !== "en" && (
                    <span className="ml-1 px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 uppercase text-[10px]">
                      {msg.language}
                    </span>
                  )}
                </div>
              )}
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed text-left whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-500 text-white rounded-tr-sm"
                    : "bg-slate-100 text-slate-800 rounded-tl-sm"
                }`}
                dangerouslySetInnerHTML={{ __html: formatText(msg.content) }}
              />

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1 justify-start">
                  {msg.sources.map((s) => (
                    <span
                      key={s}
                      className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700"
                    >
                      📄 {s.replace(".md", "")}
                    </span>
                  ))}
                </div>
              )}

              {/* Suggested actions */}
              {msg.suggested_actions && msg.suggested_actions.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.suggested_actions.map((a, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(a.replace(/^\d+\.\s*/, ""))}
                      className="block text-xs text-left w-full px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-arena-400 hover:text-arena-700 transition-colors"
                    >
                      → {a}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
              <BotIcon size={14} className="text-slate-500" />
            </div>
            <div className="bg-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2 text-slate-500 text-sm">
              <LoaderIcon size={14} className="animate-spin" />
              Thinking...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-slate-200 p-3 flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            className="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-arena-500 focus:border-arena-500"
            style={{ minHeight: 48, maxHeight: 120 }}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="flex-shrink-0 w-10 h-10 rounded-xl bg-arena-600 text-white flex items-center justify-center hover:bg-arena-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <SendIcon size={16} />
        </button>
        <span title="ArenaMind Matchday Assistant">
          <InfoIcon size={14} className="text-slate-400 flex-shrink-0" />
        </span>
      </div>
    </div>
  );
}