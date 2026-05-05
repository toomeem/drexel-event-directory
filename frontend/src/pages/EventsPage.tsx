import { useEffect, useState } from "react";
import { EventCard } from "../components/EventCard";
import { fetchEvents, type DrexelEvent } from "../api/events";

type Status = "loading" | "ready" | "error";

const EVENT_ROWS_PER_PAGE = 6;
const EVENTS_PER_ROW = 4;

export function EventsPage() {
  const [events, setEvents] = useState<DrexelEvent[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [currentPage, setCurrentPage] = useState(1);

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
  const eventCount = EVENTS_PER_ROW * EVENT_ROWS_PER_PAGE;
  const totalPages = Math.ceil(events.length / eventCount);
  const pageStart = (currentPage - 1) * eventCount;
  const pageEvents = events.slice(pageStart, pageStart + eventCount);

  function goToPage(page: number) {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="events-page">
      <div className="event-grid">
        {pageEvents.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>
      <div className="pagination">
        <button
          className="pagination__btn"
          onClick={() => goToPage(currentPage - 1)}
          disabled={currentPage === 1}
        >
          Previous
        </button>
        <span className="pagination__info">
          Page {currentPage} of {totalPages}
        </span>
        <button
          className="pagination__btn"
          onClick={() => goToPage(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}
