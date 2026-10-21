import ReactMarkdown from "react-markdown";
import type { ApiError, TravelPlan } from "@/lib/travelApi";

type Props = {
  plan: TravelPlan | null;
  error: ApiError | null;
};

// Temporary view: 3.4 replaces this with the real results UI.
export default function TripResult({ plan, error }: Props) {
  if (error) {
    return (
      <div role="alert">
        <p>{error.message}</p>
        <ul>
          {Object.entries(error.fields).map(([field, msg]) => (
            <li key={field}>
              {field}: {msg}
            </li>
          ))}
        </ul>
      </div>
    );
  }
  if (!plan) return null;

  const { name, region, country } = plan.location;
  return (
    <section>
      <h2>{[name, region !== name ? region : null, country].filter(Boolean).join(", ")}</h2>
      <p>
        Weather: {plan.weather.status} · Attractions: {plan.attractions.status}
      </p>
      {/* react-markdown doesn't render raw HTML, so model output can't inject markup */}
      <ReactMarkdown>{plan.recommendation}</ReactMarkdown>
    </section>
  );
}
