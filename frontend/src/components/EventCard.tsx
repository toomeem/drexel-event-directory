import { useState } from "react";
import type { DrexelEvent } from "../api/events";

interface EventCardProps {
  event: DrexelEvent;
}

export function EventCard({ event }: EventCardProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = event.image_url && !imageFailed;

  return (
    <article className="event-card">
      <div className="event-card__media">
        {showImage ? (
          <img
            className="event-card__image"
            src={event.image_url ?? undefined}
            alt=""
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="event-card__image-placeholder" aria-hidden="true" />
        )}
      </div>
      <div className="event-card__body">
        <p className="event-card__time">{event.time}</p>
        <h3 className="event-card__title">{event.name}</h3>
        <p className="event-card__location">{event.location}</p>
        <p className="event-card__host">Hosted by {event.org_name}</p>
      </div>
    </article>
  );
}
