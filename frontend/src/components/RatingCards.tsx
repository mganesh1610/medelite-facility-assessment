import { Activity, ClipboardCheck, HeartPulse, Users } from "lucide-react";
import type { RatingCard } from "../types";

const icons = [ClipboardCheck, HeartPulse, Users, Activity];

export function RatingCards({ ratings }: { ratings: RatingCard[] }) {
  return (
    <section className="rating-grid" aria-label="CMS star ratings">
      {ratings.map((rating, index) => {
        const Icon = icons[index] ?? ClipboardCheck;
        return (
          <article className="rating-card" key={rating.label}>
            <div className="card-icon">
              <Icon size={20} aria-hidden="true" />
            </div>
            <div>
              <span>{rating.label}</span>
              <strong>{rating.value ?? "N/A"}</strong>
              <div className="stars" aria-label={`${rating.value ?? 0} out of 5`}>
                {Array.from({ length: 5 }).map((_, starIndex) => (
                  <i key={starIndex} className={rating.value && starIndex < rating.value ? "filled" : ""} />
                ))}
              </div>
            </div>
          </article>
        );
      })}
    </section>
  );
}

