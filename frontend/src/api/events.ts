import { sampleEvents } from "../data/sampleEvents";

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
  // TODO: replace with live AWS Lambda endpoint once available.
  const response: EventsResponse = {
    statusCode: 200,
    body: sampleEvents,
  };
  return response.body;
}
