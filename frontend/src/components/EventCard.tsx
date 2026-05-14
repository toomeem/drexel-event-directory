import { useState } from "react";
import type { DrexelEvent } from "../api/events";

interface EventCardProps {
  event: DrexelEvent;
}

function formatPerk(perk: string): string {
  return perk
    .split(/[\s_]+/)
    .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w))
    .join(" ");
}

function isLive(event: DrexelEvent): boolean {
  if (!event.start_time || !event.end_time) return false;
  const now = Date.now() / 1000;
  return now >= event.start_time && now <= event.end_time;
}

function safeHttpUrl(raw: string | null | undefined): string | null {
  if (!raw) return null;
  try {
    const u = new URL(raw, window.location.origin);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.toString();
  } catch {
    return null;
  }
}

export function EventCard({ event }: EventCardProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const showImage = event.image_url && !imageFailed;
  const live = isLive(event);
  const safeLink = safeHttpUrl(event.event_link);

  const handleClick = () => {
    if (!safeLink) return;
    window.open(safeLink, "_blank", "noopener,noreferrer");
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
        {(live || (Array.isArray(event.perks) && event.perks.length > 0) || event.event_status === "virtual" || event.event_status === "hybrid") && (
          <ul className="event-card__perks">
            {live && (
              <li className="event-card__perk event-card__perk--live">
                <span className="event-card__perk-live-dot" aria-hidden="true" />
                Live
              </li>
            )}
            {event.event_status === "virtual" && (
              <li className="event-card__perk event-card__perk--virtual">Virtual</li>
            )}
            {event.event_status === "hybrid" && (
              <li className="event-card__perk event-card__perk--hybrid">Hybrid</li>
            )}
            {Array.isArray(event.perks) && event.perks.map((perk) => (
              <li key={perk} className="event-card__perk">{formatPerk(perk)}</li>
            ))}
          </ul>
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
