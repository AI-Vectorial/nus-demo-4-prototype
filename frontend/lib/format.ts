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
