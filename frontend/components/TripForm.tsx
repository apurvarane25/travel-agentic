"use client";
import { useState, type FormEvent } from "react";
import type { TravelRequest } from "@/lib/travelApi";

type Props = {
  onSubmit: (request: TravelRequest) => void;
  loading: boolean;
};

export default function TripForm({ onSubmit, loading }: Props) {
  const [city, setCity] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit({ city, start_date: startDate, end_date: endDate || null });
  }

  return (
    <form onSubmit={handleSubmit}>
      <input placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} required />
      <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
      <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      <button type="submit" disabled={loading}>
        {loading ? "Planning..." : "Plan my trip"}
      </button>
    </form>
  );
}
