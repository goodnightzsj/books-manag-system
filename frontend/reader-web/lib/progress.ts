import { api } from "./api";

/** Locator JSON shape mirrors backend `app/schemas/reading.py`. */
export type Locator =
  | { type: "pdf"; page: number; zoom?: number }
  | { type: "epub"; cfi: string; chapter?: string; progression?: number }
  | { type: "txt"; line: number; column?: number };

export type ProgressPayload = {
  progress_percent?: number;
  current_page?: number;
  total_pages?: number;
  status?: "reading" | "completed" | "plan_to_read";
  locator?: Locator;
};

/**
 * Debounced progress push. Callers should hold onto the returned
 * `push` function for the lifetime of a reading session.
 */
export function makeProgressSync(bookId: string, delayMs = 1200) {
  let timer: number | null = null;
  let pending: ProgressPayload | null = null;

  function flush() {
    if (pending) {
      const payload = pending;
      pending = null;
      api.putProgress(bookId, payload).catch((err) => {
        console.error("progress put failed", err);
      });
    }
  }

  function push(patch: ProgressPayload) {
    pending = { ...(pending ?? {}), ...patch };
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(flush, delayMs);
  }

  function flushNow() {
    if (timer) {
      window.clearTimeout(timer);
      timer = null;
    }
    flush();
  }

  return { push, flushNow };
}
