"use client";

import beyondForecast from "@/tests/fixtures/beyond-forecast.json";
import ok from "@/tests/fixtures/ok.json";
import unknownCity from "@/tests/fixtures/unknown-city.json";
import weatherFailed from "@/tests/fixtures/weather-failed.json";
import TripForm from "@/components/TripForm";
import TripResult from "@/components/TripResult";
import { ApiError, type TravelPlan, type TravelRequest } from "@/lib/travelApi";

const noOp = () => { };
const samplePlan = (value: unknown) => value as TravelPlan;
const cityIssue = unknownCity.detail[0];
const validationError = new ApiError(cityIssue.msg, 422, { city: cityIssue.msg });
const serverError = new ApiError("The planning service is temporarily unavailable. Please try again.", 502);

function StateSection({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <section className="space-y-3 border-t pt-6">
            <h2 className="text-lg font-semibold">{title}</h2>
            {children}
        </section>
    );
}

export default function StatesShowcase() {
    const request: TravelRequest = {
        city: "Xyzzyqqplorf",
        start_date: "2026-10-21",
        end_date: null,
    };

    return (
        <main className="mx-auto w-full max-w-3xl space-y-8 px-4 py-8">
            <header>
                <h1 className="text-3xl font-semibold">Trip planner states</h1>
            </header>
            <StateSection title="Successful plan">
                <TripResult plan={samplePlan(ok)} error={null} loading={false} onRetry={noOp} />
            </StateSection>
            <StateSection title="Forecast unavailable">
                <TripResult plan={samplePlan(beyondForecast)} error={null} loading={false} onRetry={noOp} />
            </StateSection>
            <StateSection title="Weather service error">
                <TripResult plan={samplePlan(weatherFailed)} error={null} loading={false} onRetry={noOp} />
            </StateSection>
            <StateSection title="Unknown city validation">
                <TripForm
                    onSubmit={noOp}
                    loading={false}
                    error={validationError}
                    initialValues={request}
                />
            </StateSection>
            <StateSection title="Loading">
                <TripResult plan={null} error={null} loading onRetry={noOp} />
            </StateSection>
            <StateSection title="Request failed">
                <TripResult plan={null} error={serverError} loading={false} onRetry={noOp} />
            </StateSection>
        </main>
    );
}