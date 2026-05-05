import { useEffect, useState } from "react";
import { EventCard } from "../components/EventCard";
import { fetchEvents, type DrexelEvent } from "../api/events";

type Status = "loading" | "ready" | "error";

export function EventsPage() {
  const [events, setEvents] = useState<DrexelEvent[]>([]);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    let cancelled = false;
    fetchEvents()
      .then((data) => {
        if (cancelled) return;
        setEvents(data);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        console.error("[EventsPage] fetchEvents failed:", err);
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return <p className="events-page__status">Loading events…</p>;
  }
  if (status === "error") {
    return (
      <p className="events-page__status events-page__status--error">
        Couldn’t load events. Please try again later.
      </p>
    );
  }
  if (events.length === 0) {
    return <p className="events-page__status">No events found.</p>;
  }

  return (
    <div className="event-grid">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}
