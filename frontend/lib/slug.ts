/**
 * A section's anchor, derived from its heading -- never from its position.
 * REQ-U15: the two travel policy versions number their sections differently,
 * so a citation can only find its section by the heading it carries.
 */
export function slug(heading: string): string {
  return heading
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function sectionHref(documentId: string, version: string, heading: string): string {
  return `/corpus/${encodeURIComponent(documentId)}?version=${encodeURIComponent(version)}#${slug(heading)}`;
}
