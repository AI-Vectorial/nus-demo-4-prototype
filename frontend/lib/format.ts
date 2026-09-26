/**
 * Presentation helpers. Nothing here talks to the network.
 */

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

/**
 * "2026-04-01" -> "1 Apr 2026".
 *
 * Formatted by hand rather than with toLocaleDateString, because the locale a
 * date is formatted in differs between the server render and the browser, and
 * a date that changes between the two is a hydration mismatch. A policy's
 * effective date is also not a moment -- parsing it into a Date would drag a
 * timezone in and move it a day.
 */
export function formatEffective(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;

  const [, year, month, day] = match;
  const name = MONTHS[Number(month) - 1];
  if (!name) return iso;

  return `${Number(day)} ${name} ${year}`;
}

/** A stable DOM id for a section heading, so the section rail can link to it. */
export function sectionSlug(heading: string, index: number): string {
  const slug = heading
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  // The index keeps it unique even when two headings normalise to the same text.
  return `section-${index + 1}${slug ? `-${slug}` : ""}`;
}

/** Split policy text into paragraphs on blank lines, dropping empty runs. */
export function paragraphs(text: string): string[] {
  return text
    .split(/\n\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);
}

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/**
 * A timestamp read as an instant.
 *
 * A stamp that arrives without an offset is UTC on the wire; JavaScript reads
 * one as local time, which moves a conversation by however many hours the
 * reader is from Greenwich.
 */
function instant(iso: string): Date | null {
  const stamped = /(?:Z|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`;
  const moment = new Date(stamped);
  return Number.isNaN(moment.getTime()) ? null : moment;
}

function ago(count: number, unit: string): string {
  return `${count} ${unit}${count === 1 ? "" : "s"} ago`;
}

/**
 * "2 hours ago", and the date itself once that stops being useful.
 *
 * Written here rather than with Intl.RelativeTimeFormat, which is a locale
 * away from the hand-formatted dates above it, or with a date library, which
 * is a dependency for eleven lines. Past a week "8 days ago" is harder to
 * place than the date, so it becomes the date.
 *
 * Only ever called from a client component: the answer changes with the wall
 * clock, so rendering it on the server would be a hydration mismatch.
 */
export function relativeTime(iso: string, from: Date = new Date()): string {
  const moment = instant(iso);
  if (!moment) return iso;

  const elapsed = from.getTime() - moment.getTime();
  // Negative when the server clock is ahead of the browser's. "In 3 seconds"
  // is noise, not information.
  if (elapsed < MINUTE) return "just now";
  if (elapsed < HOUR) return ago(Math.floor(elapsed / MINUTE), "minute");
  if (elapsed < DAY) return ago(Math.floor(elapsed / HOUR), "hour");
  if (elapsed < 7 * DAY) return ago(Math.floor(elapsed / DAY), "day");
  return formatEffective(iso.slice(0, 10));
}
