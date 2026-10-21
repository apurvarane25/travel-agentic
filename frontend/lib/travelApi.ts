import type { components } from "@/lib/api/schema";

export type TravelRequest = components["schemas"]["TravelRequest"];
export type TravelPlan = components["schemas"]["TravelPlan"];
export type TripField = keyof TravelRequest;

/** A failed request, with messages ready to show. `fields` maps form inputs to their error. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly fields: Partial<Record<TripField, string>> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// FastAPI's 422 shape; the backend's city_not_found error uses the same shape.
type ValidationIssue = { loc: (string | number)[]; msg: string; type: string };

const TRIP_FIELDS: TripField[] = ["city", "start_date", "end_date"];

export async function fetchTravelPlan(request: TravelRequest, signal?: AbortSignal): Promise<TravelPlan> {
  let res: Response;
  try {
    // Same-origin: next.config.ts proxies /api/* to the FastAPI backend.
    res = await fetch("/api/travel-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) throw err;
    throw new ApiError("Couldn't reach the server. Check your connection and try again.", 0);
  }

  if (res.ok) return (await res.json()) as TravelPlan;

  const detail: unknown = await res
    .json()
    .then((body) => body?.detail)
    .catch(() => undefined);

  if (res.status === 422 && Array.isArray(detail)) {
    const fields: ApiError["fields"] = {};
    let formMessage: string | undefined;
    for (const issue of detail as ValidationIssue[]) {
      const msg = issue.msg.replace(/^Value error, /, "");
      const field = issue.loc[1];
      if (typeof field === "string" && TRIP_FIELDS.includes(field as TripField)) {
        fields[field as TripField] ??= msg;
      } else {
        formMessage ??= msg; // model-level checks (e.g. date order) have loc ["body"]
      }
    }
    throw new ApiError(formMessage ?? "Please check the highlighted fields.", 422, fields);
  }

  if ((res.status === 502 || res.status === 503) && typeof detail === "string") {
    throw new ApiError(detail, res.status);
  }
  throw new ApiError(`Something went wrong (error ${res.status}). Please try again.`, res.status);
}
