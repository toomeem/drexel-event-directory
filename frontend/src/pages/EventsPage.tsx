import { useEffect, useMemo, useState } from "react";

import { useSearchParams } from "react-router-dom";
import { EventCard, EventCardSkeleton } from "../components/EventCard";
import {
  EventFilterBar,
  EventSidebarFilters,
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
const VALID_STATUSES: EventStatus[] = ["in-person", "online", "hybrid"];

function parseFilters(searchParams: URLSearchParams): AppliedFilters {
  const dateRaw = searchParams.get("dateRange");
  const statusRaw = searchParams.get("event_status");
  const themeRaw = searchParams.get("theme");
  const perksRaw = searchParams.get("perks");
  const religionRaw = searchParams.get("religion");
  const searchRaw = searchParams.get("search");
  return {
    search: searchRaw ?? "",
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
    foodRelated: searchParams.get("food_related") === "true",
    popular: searchParams.get("popular") === "true",
    recurring:
      searchParams.get("recurring") === "true" ||
      searchParams.get("weekly") === "true",
    forNewStudents: searchParams.get("for_new_students") === "true",
    onCampus: searchParams.get("on_campus") === "true",
    religion: religionRaw
      ? religionRaw.split(",").map((r) => r.trim().toLowerCase()).filter(Boolean)
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
  const religionKey = filters.religion.join(",");
  const searchKey = filters.search;

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    fetchEvents(currentPage, eventCount, {
      dateRange: dateRange as DateRange | undefined,
      eventStatus: eventStatus as EventStatus | undefined,
      themes: themesKey ? themesKey.split(",") : undefined,
      perks: perksKey ? perksKey.split(",") : undefined,
      search: searchKey || undefined,
      food_related: filters.foodRelated || undefined,
      popular: filters.popular || undefined,
      recurring: filters.recurring || undefined,
      for_new_students: filters.forNewStudents || undefined,
      on_campus: filters.onCampus || undefined,
      religion: religionKey ? religionKey.split(",") : undefined,
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
  }, [
    currentPage,
    eventCount,
    dateRange,
    eventStatus,
    themesKey,
    perksKey,
    searchKey,
    filters.foodRelated,
    filters.popular,
    filters.recurring,
    filters.forNewStudents,
    filters.onCampus,
    religionKey,
  ]);

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
    if (newFilters.search.trim()) {
      next.set("search", newFilters.search.trim());
    }
    if (newFilters.foodRelated) next.set("food_related", "true");
    if (newFilters.popular) next.set("popular", "true");
    if (newFilters.recurring) next.set("recurring", "true");
    if (newFilters.forNewStudents) next.set("for_new_students", "true");
    if (newFilters.onCampus) next.set("on_campus", "true");
    if (newFilters.religion.length > 0) next.set("religion", newFilters.religion.join(","));
    setSearchParams(next, { replace: true });
  }

  return (
    <div className="events-page">
      <EventFilterBar
        filters={filters}
        totalEvents={totalEvents}
        onChange={applyFilters}
      />
      <div className="events-page__layout">
        <EventSidebarFilters filters={filters} onChange={applyFilters} />
        <div className="events-page__content">
          {status === "loading" && (
            <div className="event-grid">
              {Array.from({ length: eventCount }, (_, i) => (
                <EventCardSkeleton key={i} />
              ))}
            </div>
          )}
          {status === "error" && (
            <p className="events-page__status events-page__status--error">
              Couldn't load events. Please try again later.
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
                <div className="pagination__pages">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                    (page) => (
                      <button
                        key={page}
                        className={
                          page === currentPage
                            ? "pagination__page pagination__page--active"
                            : "pagination__page"
                        }
                        onClick={() => goToPage(page)}
                        aria-current={page === currentPage ? "page" : undefined}
                      >
                        {page}
                      </button>
                    )
                  )}
                </div>
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
      </div>
    </div>
  );
}
