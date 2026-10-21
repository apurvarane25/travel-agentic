"use client";
import TripForm from "@/components/TripForm";
import TripResult from "@/components/TripResult";
import { useTravelPlan } from "@/hooks/useTravelPlan";

export default function Home() {
  const { plan, error, loading, getPlan } = useTravelPlan();

  return (
    <main className="mx-auto my-10 w-full max-w-2xl p-4">
      <h1>Travel Planner</h1>
      <TripForm onSubmit={getPlan} loading={loading} />
      <TripResult plan={plan} error={error} />
    </main>
  );
}
