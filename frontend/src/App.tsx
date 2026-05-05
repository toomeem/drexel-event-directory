import { Route, Routes } from "react-router-dom";
import { SiteHeader } from "./components/SiteHeader";
import { EventsPage } from "./pages/EventsPage";
import { AboutPage } from "./pages/AboutPage";

export function App() {
  return (
    <div className="app">
      <SiteHeader />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<EventsPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>
    </div>
  );
}
