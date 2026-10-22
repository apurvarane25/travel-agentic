import { useRef, useState } from "react";
import { ApiError, fetchTravelPlan, type TravelPlan, type TravelRequest } from "@/lib/travelApi";

export function useTravelPlan() {
  const [plan, setPlan] = useState<TravelPlan | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);
  const inFlight = useRef<AbortController | null>(null);
  const lastRequest = useRef<TravelRequest | null>(null);

  async function getPlan(request: TravelRequest) {
    inFlight.current?.abort(); // a new search cancels the previous one
    lastRequest.current = request;
    const controller = new AbortController();
    inFlight.current = controller;

    setLoading(true);
    setError(null);
    setPlan(null);
    try {
      setPlan(await fetchTravelPlan(request, controller.signal));
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof ApiError ? err : new ApiError("Something went wrong. Please try again.", 0));
    } finally {
      if (inFlight.current === controller) setLoading(false);
    }
  }

  function retry() {
    if (lastRequest.current) void getPlan(lastRequest.current);
  }

  return { plan, error, loading, getPlan, retry };
}
