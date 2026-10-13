"use client";
import TripForm from "@/components/TripForm";
import TripResult from "@/components/TripResult";
import { useTravelPlan } from "@/hooks/useTravelPlan";

export default function Home() {
  const { result, error, loading, getPlan } = useTravelPlan();

  return (
    <main style={{ maxWidth: 700, margin: "40px auto", padding: 16 }}>
      <h1>Travel Planner</h1>
      <TripForm onSubmit={getPlan} loading={loading} />
      <TripResult result={result} error={error} />
    </main>
  );
}