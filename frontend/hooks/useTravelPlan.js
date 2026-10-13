import { useState } from "react";
import { fetchTravelPlan } from "@/lib/travelApi";

export function useTravelPlan() {
    const [result, setResult] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function getPlan(trip) {
        setLoading(true);
        setError("");
        setResult("");
        try {
            const plan = await fetchTravelPlan(trip);
            setResult(plan);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return { result, error, loading, getPlan };
}