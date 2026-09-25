/**
 * A small Markdown renderer for exactly what the corpus is written in.
 * REQ-U12.
 *
 * Not a Markdown library. The policies use headings, paragraphs, tables,
 * bullets, block quotes, rules and inline emphasis -- nothing else -- and a
 * dependency that handles CommonMark, footnotes and HTML passthrough would be
 * a large surface for a small job, on a page that renders text we control.
 *
 * It returns React elements, never HTML: nothing here has to be escaped by
 * hand, and there is no dangerouslySetInnerHTML for a policy author to trip
 * over. The parser is line by line -- a table starts at a line beginning with
 * "|" and ends at the first line that does not.
 *
 * The tables are the reason this exists. They carry the approval thresholds,
 * the accommodation caps and the retention periods, and printed as raw pipes
 * and dashes a reader cannot check the citation -- which is the only reason
 * the corpus browser is in the product.
 */

import type { ReactNode } from "react";

/* -------------------------------------------------------------------------
   Inline: **bold**, *italic*, `code`.
   ------------------------------------------------------------------------- */

const INLINE = "`([^`]+)`|\\*\\*([\\s\\S]+?)\\*\\*|\\*([^*\\n]+)\\*";

/**
 * The inline pass on its own.
 *
 * Exported because an answer from /ask carries bold too, and a bold marker
 * rendered as literal asterisks reads as a broken product.
 */
export function inlineMarkdown(text: string, keyPrefix = "i"): ReactNode[] {
  const nodes: ReactNode[] = [];
  // Its own regex, not a shared one: /g carries a lastIndex, this function
  // recurses into bold and italic, and a shared cursor reset by the inner call
  // leaves the outer loop matching the same characters for ever.
  const pattern = new RegExp(INLINE, "g");

  let last = 0;
  let count = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const key = `${keyPrefix}-${count++}`;

    if (match[1] !== undefined) {
      // Code is literal: no emphasis is parsed inside it.
      nodes.push(
        <code key={key} className="md-code">
          {match[1]}
        </code>,
      );
    } else if (match[2] !== undefined) {
      nodes.push(<strong key={key}>{inlineMarkdown(match[2], key)}</strong>);
    } else {
      nodes.push(<em key={key}>{inlineMarkdown(match[3] ?? "", key)}</em>);
    }

    last = pattern.lastIndex;
  }

  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

/** The inline pass as a component, for a paragraph that is already split. */
export function InlineMarkdown({ text }: { text: string }) {
  return <>{inlineMarkdown(text)}</>;
}

/* -------------------------------------------------------------------------
   Blocks.
   ------------------------------------------------------------------------- */

const RULE = /^-{3,}$/;
const BULLET = /^[-*]\s+/;
const QUOTE = /^>\s?/;

/** "| a | b |" -> ["a", "b"]. The outer pipes are optional in the corpus. */
function cells(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

/** The "|---|---|" line under a header row, with optional alignment colons. */
function isDivider(line: string): boolean {
  const body = line.trim();
  return body.startsWith("|") && /^[\s|:-]+$/.test(body) && body.includes("-");
}

/** Does this line start a block that is not a paragraph? */
function startsBlock(line: string): boolean {
  const body = line.trim();
  return (
    body === "" ||
    body.startsWith("|") ||
    body.startsWith("#") ||
    BULLET.test(body) ||
    QUOTE.test(body) ||
    RULE.test(body)
  );
}

/**
 * Parse a section's raw text into React nodes.
 *
 * The loop owns one index. Every branch consumes the lines it used and leaves
 * `i` on the first line it did not, so an unrecognised line always falls
 * through to a paragraph rather than being dropped.
 */
export function renderMarkdown(text: string): ReactNode[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];
    const body = line.trim();

    if (body === "") {
      i += 1;
      continue;
    }

    // A horizontal rule.
    if (RULE.test(body)) {
      blocks.push(<hr key={`r${key++}`} className="md-rule" />);
      i += 1;
      continue;
    }

    // Headings. The section's own heading is the h2 around this text, so what
    // is inside it starts one level down.
    if (body.startsWith("### ")) {
      const heading = body.slice(4).trim();
      blocks.push(
        <h4 key={`h${key++}`} className="md-h3">
          {inlineMarkdown(heading, `h${key}`)}
        </h4>,
      );
      i += 1;
      continue;
    }

    if (body.startsWith("## ")) {
      const heading = body.slice(3).trim();
      blocks.push(
        <h3 key={`h${key++}`} className="md-h2">
          {inlineMarkdown(heading, `h${key}`)}
        </h3>,
      );
      i += 1;
      continue;
    }

    // A table: every consecutive line that begins with a pipe.
    if (body.startsWith("|")) {
      const rows: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        rows.push(lines[i]);
        i += 1;
      }

      const hasHeader = rows.length > 1 && isDivider(rows[1]);
      const head = hasHeader ? cells(rows[0]) : null;
      const bodyRows = (hasHeader ? rows.slice(2) : rows)
        .filter((row) => !isDivider(row))
        .map(cells);

      const tableKey = `t${key++}`;
      blocks.push(
        <div key={tableKey} className="md-table-wrap">
          <table className="md-table">
            {head && (
              <thead>
                <tr>
                  {head.map((cell, index) => (
                    <th key={`${tableKey}-h${index}`} scope="col">
                      {inlineMarkdown(cell, `${tableKey}-h${index}`)}
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {bodyRows.map((row, rowIndex) => (
                <tr key={`${tableKey}-${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`${tableKey}-${rowIndex}-${cellIndex}`}>
                      {inlineMarkdown(cell, `${tableKey}-${rowIndex}-${cellIndex}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // A bullet list. A wrapped item continues on an indented line, which is
    // how the corpus writes anything longer than one line.
    if (BULLET.test(body)) {
      const items: string[] = [];
      while (i < lines.length) {
        const current = lines[i];
        if (BULLET.test(current.trim())) {
          items.push(current.trim().replace(BULLET, ""));
          i += 1;
        } else if (
          items.length > 0 &&
          current.trim() !== "" &&
          /^\s/.test(current)
        ) {
          items[items.length - 1] += ` ${current.trim()}`;
          i += 1;
        } else {
          break;
        }
      }

      const listKey = `u${key++}`;
      blocks.push(
        <ul key={listKey} className="md-list">
          {items.map((item, index) => (
            <li key={`${listKey}-${index}`}>
              {inlineMarkdown(item, `${listKey}-${index}`)}
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    // A block quote, which the corpus uses for the notes beside a rule.
    if (QUOTE.test(body)) {
      const quoted: string[] = [];
      while (i < lines.length && QUOTE.test(lines[i].trim())) {
        quoted.push(lines[i].trim().replace(QUOTE, ""));
        i += 1;
      }

      const quoteKey = `q${key++}`;
      blocks.push(
        <blockquote key={quoteKey} className="md-quote">
          <p>{inlineMarkdown(quoted.join(" "), quoteKey)}</p>
        </blockquote>,
      );
      continue;
    }

    // Anything else is a paragraph, running to the next blank line or the
    // start of the next block.
    const paragraph: string[] = [line.trim()];
    i += 1;
    while (i < lines.length && !startsBlock(lines[i])) {
      paragraph.push(lines[i].trim());
      i += 1;
    }

    const paraKey = `p${key++}`;
    blocks.push(<p key={paraKey}>{inlineMarkdown(paragraph.join(" "), paraKey)}</p>);
  }

  return blocks;
}

/** The whole of it as a component: `<Markdown text={section.text} />`. */
export default function Markdown({ text }: { text: string }) {
  return <>{renderMarkdown(text)}</>;
}
