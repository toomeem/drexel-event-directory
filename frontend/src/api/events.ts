export type EventSource = "drexel_events" | "dragonlink" | "drexel_athletics";
export type EventStatus = "in-person" | "online" | "hybrid";
export type DateRange = "today" | "week" | "month";

export interface DrexelEvent {
  id: string;
  source: EventSource | string;
  name: string;
  org_name: string;
  location: string;
  time: string;
  start_time?: number | null;
  end_time?: number | null;
  image_url: string | null;
  event_link: string;
  event_status?: EventStatus | string | null;
  theme?: string | null;
  perks?: string[];
  food_related?: boolean;
  popular?: boolean;
  weekly?: boolean;
  for_new_students?: boolean;
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
  food_related?: boolean;
  popular?: boolean;
  weekly?: boolean;
  for_new_students?: boolean;
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
  if (filters.food_related) params.set("food_related", "true");
  if (filters.popular) params.set("popular", "true");
  if (filters.weekly) params.set("weekly", "true");
  if (filters.for_new_students) params.set("for_new_students", "true");
  const url = `${endpoint}?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  const data: EventsResponse = await res.json();
  return { events: data.body, totalEvents: data.total_events };
}
