"use client";
import TripForm from "@/components/TripForm";
import TripResult from "@/components/TripResult";
import { useTravelPlan } from "@/hooks/useTravelPlan";

export default function Home() {
  const { plan, error, loading, getPlan, retry } = useTravelPlan();

  return (
    <main className="mx-auto w-full max-w-3xl space-y-8 px-4 py-8 md:py-12">
      <header className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">Your next trip, thoughtfully planned</p>
        <h1 className="text-3xl font-semibold">Travel Planner</h1>
      </header>
      <TripForm onSubmit={getPlan} loading={loading} error={error} />
      <TripResult plan={plan} error={error} loading={loading} onRetry={retry} />
    </main>
  );
}
