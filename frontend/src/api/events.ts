export type EventSource = "drexel_events" | "dragonlink" | "drexel_athletics";

export interface DrexelEvent {
  id: string;
  source: EventSource | string;
  name: string;
  org_name: string;
  location: string;
  time: string;
  image_url: string | null;
}

interface EventsResponse {
  statusCode: number;
  body: DrexelEvent[];
}

export async function fetchEvents(): Promise<DrexelEvent[]> {
  const endpoint = import.meta.env.VITE_LAMBDA_ENDPOINT;
  console.log("[fetchEvents] endpoint:", endpoint);
  const res = await fetch(endpoint);
  console.log("[fetchEvents] response status:", res.status, res.statusText);
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  const data: EventsResponse = await res.json();
  console.log("[fetchEvents] data:", data);
  return data.body;
}
