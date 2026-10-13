"use client";
import { useState } from "react";

export default function TripForm({ onSubmit, loading }) {
    const [city, setCity] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");

    function handleSubmit(e) {
        e.preventDefault();
        onSubmit({ city, startDate, endDate });
    }

    return (
        <form onSubmit={handleSubmit}>
            <input
                placeholder="City"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
            />
            <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
            />
            <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? "Planning..." : "Plan my trip"}
            </button>
        </form>
    );
}