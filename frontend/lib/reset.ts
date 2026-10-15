/**
 * The Reset action in the top bar tells the open conversation to start again.
 * A window event, because the bar and the conversation are separate components
 * and Reset must work from any route (REQ-U9, REQ-C6).
 */
export const RESET_EVENT = "policy-assistant:reset";

export function requestReset(): void {
  window.dispatchEvent(new Event(RESET_EVENT));
}
