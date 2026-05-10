import { useEffect, useMemo, useState } from "react";

import { useSearchParams } from "react-router-dom";
import { EventCard } from "../components/EventCard";
import {
  EventFilterBar,
  type AppliedFilters,
} from "../components/EventFilterBar";
import {
  fetchEvents,
  type DateRange,
  type DrexelEvent,
  type EventStatus,
} from "../api/events";

type Status = "loading" | "ready" | "error";

const EVENT_ROWS_PER_PAGE = 6;
const EVENTS_PER_ROW = 4;

const VALID_DATE_RANGES: DateRange[] = ["today", "week", "month"];
const VALID_STATUSES: EventStatus[] = ["in-person", "virtual", "hybrid"];

function parseFilters(searchParams: URLSearchParams): AppliedFilters {
  const dateRaw = searchParams.get("dateRange");
  const statusRaw = searchParams.get("event_status");
  const themeRaw = searchParams.get("theme");
  const perksRaw = searchParams.get("perks");
  return {
    dateRange:
      dateRaw && (VALID_DATE_RANGES as string[]).includes(dateRaw)
        ? [dateRaw]
        : [],
    eventStatus:
      statusRaw && (VALID_STATUSES as string[]).includes(statusRaw)
        ? [statusRaw]
        : [],
    themes: themeRaw
      ? themeRaw
          .split(",")
          .map((t) => t.trim().toLowerCase())
          .filter(Boolean)
      : [],
    perks: perksRaw
      ? perksRaw
          .split(",")
          .map((p) => p.trim().toLowerCase())
          .filter(Boolean)
      : [],
  };
}

export function EventsPage() {
  const [events, setEvents] = useState<DrexelEvent[]>([]);
  const [totalEvents, setTotalEvents] = useState(0);
  const [status, setStatus] = useState<Status>("loading");
  const [searchParams, setSearchParams] = useSearchParams();

  const currentPage = Math.max(1, Number(searchParams.get("page")) || 1);
  const eventCount = EVENTS_PER_ROW * EVENT_ROWS_PER_PAGE;

  const filters = useMemo(() => parseFilters(searchParams), [searchParams]);
  const dateRange = filters.dateRange[0];
  const eventStatus = filters.eventStatus[0];
  const themesKey = filters.themes.join(",");
  const perksKey = filters.perks.join(",");

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    fetchEvents(currentPage, eventCount, {
      dateRange: dateRange as DateRange | undefined,
      eventStatus: eventStatus as EventStatus | undefined,
      themes: themesKey ? themesKey.split(",") : undefined,
      perks: perksKey ? perksKey.split(",") : undefined,
    })
      .then(({ events: data, totalEvents: total }) => {
        if (cancelled) return;
        setEvents(data);
        setTotalEvents(total);
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
  }, [currentPage, eventCount, dateRange, eventStatus, themesKey, perksKey]);

  const totalPages = Math.max(1, Math.ceil(totalEvents / eventCount));

  function goToPage(page: number) {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(page));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function applyFilters(newFilters: AppliedFilters) {
    const next = new URLSearchParams();
    next.set("page", "1");
    if (newFilters.dateRange[0]) next.set("dateRange", newFilters.dateRange[0]);
    if (newFilters.eventStatus[0]) {
      next.set("event_status", newFilters.eventStatus[0]);
    }
    if (newFilters.themes.length > 0) {
      next.set("theme", newFilters.themes.join(","));
    }
    if (newFilters.perks.length > 0) {
      next.set("perks", newFilters.perks.join(","));
    }
    setSearchParams(next);
  }

  return (
    <div className="events-page">
      <EventFilterBar filters={filters} onChange={applyFilters} />
      {status === "loading" && (
        <p className="events-page__status">Loading events…</p>
      )}
      {status === "error" && (
        <p className="events-page__status events-page__status--error">
          Couldn’t load events. Please try again later.
        </p>
      )}
      {status === "ready" && events.length === 0 && (
        <p className="events-page__status">No events match these filters.</p>
      )}
      {status === "ready" && events.length > 0 && (
        <>
          <div className="event-grid">
            {events.map((event) => (
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
              disabled={currentPage >= totalPages}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
