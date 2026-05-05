import { useState } from "react";
import type { DrexelEvent } from "../api/events";

interface EventCardProps {
  event: DrexelEvent;
}

export function EventCard({ event }: EventCardProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = event.image_url && !imageFailed;

  const handleClick = () => {
    window.open(event.event_link, "_blank");
  };

  return (
    <article className="event-card" onClick={handleClick} role="button" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && handleClick()}>
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
        <p className="event-card__time">
          <svg className="event-card__icon" viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none"/>
            <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
          </svg>
          {event.time}
        </p>
        <h3 className="event-card__title">{event.name}</h3>
        <p className="event-card__location">
          <svg className="event-card__icon" viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">
            <path d="M12 2C7.58 2 4 5.58 4 10c0 5.25 8 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z" fill="currentColor"/>
          </svg>
          {event.location}
        </p>
        <p className="event-card__host">Hosted by <strong>{event.org_name}</strong></p>
      </div>
    </article>
  );
}
