import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { ChatbotWidget } from "./components/ChatbotWidget";
import { SiteHeader } from "./components/SiteHeader";
import { EventsPage } from "./pages/EventsPage";
import { AboutPage } from "./pages/AboutPage";

type Theme = "light" | "dark";

const AI_ENABLED_KEY = "ai:enabled";

export function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem("theme") as Theme | null;
    if (stored) return stored;
    return "light";
  });

  const [aiEnabled, setAiEnabled] = useState<boolean>(() => {
    return sessionStorage.getItem(AI_ENABLED_KEY) !== "false";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    sessionStorage.setItem(AI_ENABLED_KEY, String(aiEnabled));
  }, [aiEnabled]);

  function toggleTheme() {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  }

  function toggleAi() {
    setAiEnabled((v) => !v);
  }

  return (
    <div className="app">
      <SiteHeader
        theme={theme}
        onToggleTheme={toggleTheme}
        aiEnabled={aiEnabled}
        onToggleAi={toggleAi}
      />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<EventsPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>
      {aiEnabled && <ChatbotWidget />}
    </div>
  );
}
