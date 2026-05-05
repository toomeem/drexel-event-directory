export type EventSource = "drexel_events" | "dragonlink";

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
  const res = await fetch(endpoint);
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  const data: EventsResponse = await res.json();
  return data.body;
}
