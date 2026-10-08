/**
 * Policy text and answers are Markdown. REQ-U12: render it as markup -- the
 * tables carry the thresholds, caps and retention periods, and as raw pipes
 * and dashes nobody can check them. react-markdown + remark-gfm (both MIT)
 * were approved by the team for exactly this.
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
