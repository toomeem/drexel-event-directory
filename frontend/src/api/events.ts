export type EventSource = "drexel_events" | "dragonlink" | "drexel_athletics";

export interface DrexelEvent {
  id: string;
  source: EventSource | string;
  name: string;
  org_name: string;
  location: string;
  time: string;
  image_url: string | null;
  event_link: string;
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

export async function fetchEvents(
  page: number,
  limit: number,
): Promise<FetchEventsResult> {
  const endpoint = import.meta.env.VITE_LAMBDA_ENDPOINT;
  if (!endpoint) {
    throw new Error(
      "VITE_LAMBDA_ENDPOINT is not set — check the build env / GitHub Actions secret",
    );
  }
  console.log("[fetchEvents] endpoint:", endpoint);
  const res = await fetch(`${endpoint}?page=${page}&limit=${limit}`);
  console.log("[fetchEvents] response status:", res.status, res.statusText);
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  const data: EventsResponse = await res.json();
  console.log("[fetchEvents] data:", data);
  return { events: data.body, totalEvents: data.total_events };
}
