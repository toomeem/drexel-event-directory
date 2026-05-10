export type EventSource = "drexel_events" | "dragonlink" | "drexel_athletics";
export type EventStatus = "in-person" | "virtual" | "hybrid";
export type DateRange = "today" | "week" | "month";

export interface DrexelEvent {
  id: string;
  source: EventSource | string;
  name: string;
  org_name: string;
  location: string;
  time: string;
  image_url: string | null;
  event_link: string;
  event_status?: EventStatus | string | null;
  theme?: string | null;
  perks?: string[];
}

interface EventsResponse {
  statusCode: number;
  body: DrexelEvent[];
  total_events: number;
}

export interface FetchEventsResult {
  events: DrexelEvent[];
  totalEvents: number;
}

export interface EventFilters {
  dateRange?: DateRange;
  eventStatus?: EventStatus;
  themes?: string[];
  perks?: string[];
  search?: string;
}

export async function fetchEvents(
  page: number,
  limit: number,
  filters: EventFilters = {},
): Promise<FetchEventsResult> {
  const endpoint = import.meta.env.VITE_LAMBDA_ENDPOINT;
  if (!endpoint) {
    throw new Error(
      "VITE_LAMBDA_ENDPOINT is not set — check the build env / GitHub Actions secret",
    );
  }
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });
  if (filters.dateRange) params.set("dateRange", filters.dateRange);
  if (filters.eventStatus) params.set("event_status", filters.eventStatus);
  if (filters.themes && filters.themes.length > 0) {
    params.set("theme", filters.themes.join(","));
  }
  if (filters.perks && filters.perks.length > 0) {
    params.set("perks", filters.perks.join(","));
  }
  if (filters.search && filters.search.trim()) {
    params.set("search", filters.search.trim());
  }
  const url = `${endpoint}?${params.toString()}`;
  console.log("[fetchEvents] url:", url);
  const res = await fetch(url);
  console.log("[fetchEvents] response status:", res.status, res.statusText);
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  const data: EventsResponse = await res.json();
  console.log("[fetchEvents] data:", data);
  return { events: data.body, totalEvents: data.total_events };
}
