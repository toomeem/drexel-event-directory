import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { ChatbotWidget } from "./components/ChatbotWidget";
import { SiteHeader } from "./components/SiteHeader";
import { EventsPage } from "./pages/EventsPage";
import { AboutPage } from "./pages/AboutPage";

type Theme = "light" | "dark";

export function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem("theme") as Theme | null;
    if (stored) return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  }

  return (
    <div className="app">
      <SiteHeader theme={theme} onToggleTheme={toggleTheme} />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<EventsPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>
      <ChatbotWidget />
    </div>
  );
}
