/**
 * A small Markdown renderer for policy text and answers. REQ-U12.
 *
 * It builds React elements and never sets innerHTML, so the text it is given
 * cannot inject markup. It covers what the corpus uses: headings, paragraphs,
 * bullet and numbered lists, pipe tables, bold, and inline code.
 *
 * It is deliberately small. Adding a Markdown library is a dependency decision,
 * and this corpus does not need one.
 */

import { createElement, Fragment, type ReactNode } from "react";

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`)/g;

function inline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, index) => {
    if (part.length > 4 && part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.length > 2 && part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}

function cells(row: string): string[] {
  return row
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

const isTableRow = (line: string) => line.trim().startsWith("|");
const isSeparator = (line: string) => /^\|?\s*:?-{2,}/.test(line.trim());
const isBullet = (line: string) => /^[-*]\s+/.test(line.trim());
const isNumbered = (line: string) => /^\d+\.\s+/.test(line.trim());
const isHeading = (line: string) => /^#{1,6}\s+/.test(line.trim());
const isRule = (line: string) => /^-{3,}$/.test(line.trim());

function blocks(source: string): ReactNode[] {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const out: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed || isRule(trimmed)) {
      i++;
      continue;
    }

    if (isHeading(trimmed)) {
      const hashes = /^(#+)/.exec(trimmed)?.[1].length ?? 1;
      // The page already carries a level-two heading, so corpus headings start at three.
      const tag = hashes <= 1 ? "h3" : hashes === 2 ? "h4" : "h5";
      const text = trimmed.replace(/^#+\s+/, "");
      out.push(createElement(tag, { key: i }, inline(text)));
      i++;
      continue;
    }

    if (isTableRow(trimmed)) {
      const rows: string[] = [];
      while (i < lines.length && isTableRow(lines[i])) {
        rows.push(lines[i]);
        i++;
      }
      const header = rows[0] ? cells(rows[0]) : [];
      const body = rows.slice(1).filter((row) => !isSeparator(row));
      out.push(
        <div className="md-table-wrap" key={`t${i}`}>
          <table>
            <thead>
              <tr>
                {header.map((cell, c) => (
                  <th key={c}>{inline(cell)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, r) => (
                <tr key={r}>
                  {cells(row).map((cell, c) => (
                    <td key={c}>{inline(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    if (isBullet(trimmed) || isNumbered(trimmed)) {
      const ordered = isNumbered(trimmed);
      const items: string[] = [];
      while (i < lines.length && (ordered ? isNumbered(lines[i]) : isBullet(lines[i]))) {
        items.push(lines[i].trim().replace(ordered ? /^\d+\.\s+/ : /^[-*]\s+/, ""));
        i++;
      }
      const list = items.map((item, n) => <li key={n}>{inline(item)}</li>);
      out.push(
        ordered ? (
          <ol key={`l${i}`}>{list}</ol>
        ) : (
          <ul key={`l${i}`}>{list}</ul>
        ),
      );
      continue;
    }

    const paragraph: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !isRule(lines[i]) &&
      !isHeading(lines[i]) &&
      !isTableRow(lines[i]) &&
      !isBullet(lines[i]) &&
      !isNumbered(lines[i])
    ) {
      paragraph.push(lines[i].trim());
      i++;
    }
    out.push(<p key={`p${i}`}>{inline(paragraph.join(" "))}</p>);
  }

  return out;
}

export function Markdown({ source }: { source: string }) {
  return <div className="md">{blocks(source)}</div>;
}
