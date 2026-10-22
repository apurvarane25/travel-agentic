import { TriangleAlert } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { ApiError, TravelPlan } from "@/lib/travelApi";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

type Props = {
  plan: TravelPlan | null;
  error: ApiError | null;
  loading: boolean;
  onRetry: () => void;
};

function formatCalendarDate(value: string, options: Intl.DateTimeFormatOptions) {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat(undefined, options).format(new Date(year, month - 1, day));
}

function DateRange({ plan }: { plan: TravelPlan }) {
  return (
    <p className="text-sm text-muted-foreground">
      {formatCalendarDate(plan.start_date, { month: "long", day: "numeric", year: "numeric" })}
      {plan.start_date !== plan.end_date && (
        <> – {formatCalendarDate(plan.end_date, { month: "long", day: "numeric", year: "numeric" })}</>
      )}
    </p>
  );
}

function Warning({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <Alert variant="destructive">
      <TriangleAlert aria-hidden="true" />
      <AlertTitle>Something went wrong</AlertTitle>
      <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
        <span>{message}</span>
        <Button type="button" variant="outline" onClick={onRetry}>Try again</Button>
      </AlertDescription>
    </Alert>
  );
}

function WeatherCard({ plan, onRetry }: { plan: TravelPlan; onRetry: () => void }) {
  const weather = plan.weather;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weather</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {weather.status === "ok" && (
          <>
            {weather.days.length > 0 ? (
              <div className="divide-y">
                {weather.days.map((day) => (
                  <div key={day.day} className="grid grid-cols-[minmax(0,1fr)_auto_auto] gap-3 py-2 text-sm">
                    <span className="font-medium">
                      {formatCalendarDate(day.day, { weekday: "short", month: "short", day: "numeric" })}
                    </span>
                    <span>{day.temp_max_c}° / {day.temp_min_c}°C</span>
                    <span className="text-muted-foreground">{day.precipitation_mm} mm</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No daily forecast is available.</p>
            )}
            {weather.message && <p className="text-sm text-muted-foreground">{weather.message}</p>}
          </>
        )}
        {weather.status === "unavailable" && (
          <p className="text-sm text-muted-foreground">{weather.message ?? "Weather information is unavailable for these dates."}</p>
        )}
        {weather.status === "error" && (
          <Warning message={weather.message ?? "The weather service is unavailable."} onRetry={onRetry} />
        )}
      </CardContent>
    </Card>
  );
}

function AttractionsCard({ plan, onRetry }: { plan: TravelPlan; onRetry: () => void }) {
  const attractions = plan.attractions;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Attractions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {attractions.status === "ok" && (
          <>
            {attractions.items.length > 0 ? (
              <ul className="list-inside list-disc space-y-1 text-sm">
                {attractions.items.map((item) => <li key={item}>{item}</li>)}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No attractions were found.</p>
            )}
            {attractions.source_url && (
              <a className="text-sm underline underline-offset-4" href={attractions.source_url} target="_blank" rel="noopener noreferrer">
                Source: Wikipedia
              </a>
            )}
          </>
        )}
        {attractions.status === "unavailable" && (
          <p className="text-sm text-muted-foreground">{attractions.message ?? "Attraction information is unavailable."}</p>
        )}
        {attractions.status === "error" && (
          <Warning message={attractions.message ?? "Attraction information could not be loaded."} onRetry={onRetry} />
        )}
      </CardContent>
    </Card>
  );
}

function RecommendationCard({ recommendation }: { recommendation: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Suggested plan</CardTitle>
        <CardDescription>AI-generated; suggestions may be general.</CardDescription>
      </CardHeader>
      <CardContent className="prose prose-sm max-w-none break-words dark:prose-invert [&_a]:underline [&_h2]:mt-5 [&_h2]:text-lg [&_h3]:mt-4 [&_h3]:text-base [&_p]:my-3 [&_ul]:my-3">
        <ReactMarkdown>{recommendation}</ReactMarkdown>
      </CardContent>
    </Card>
  );
}

function LoadingCards() {
  return (
    <div className="grid gap-4 md:grid-cols-2" aria-label="Trip plan loading">
      <Card>
        <CardHeader><Skeleton className="h-5 w-24" /></CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/5" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader><Skeleton className="h-5 w-28" /></CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-4 w-3/5" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
      <Card className="md:col-span-2">
        <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/5" />
        </CardContent>
      </Card>
    </div>
  );
}

export default function TripResult({ plan, error, loading, onRetry }: Props) {
  const requestError = error && error.status !== 422 ? error : null;

  return (
    <section className="space-y-4" aria-busy={loading}>
      {loading && <p className="sr-only" role="status" aria-live="polite">Planning your trip…</p>}
      {loading && <LoadingCards />}
      {!loading && requestError && (
        <Alert variant="destructive">
          <TriangleAlert aria-hidden="true" />
          <AlertTitle>Unable to plan this trip</AlertTitle>
          <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
            <span>{requestError.message}</span>
            <Button type="button" variant="outline" onClick={onRetry}>Try again</Button>
          </AlertDescription>
        </Alert>
      )}
      {!loading && !requestError && !plan && (
        <p className="text-sm text-muted-foreground">Enter a city and dates to start planning.</p>
      )}
      {!loading && plan && (
        <div className="space-y-4">
          <header>
            <h2 className="text-xl font-semibold">
              {[plan.location.name, plan.location.region !== plan.location.name ? plan.location.region : null, plan.location.country]
                .filter(Boolean)
                .join(", ")}
            </h2>
            <DateRange plan={plan} />
          </header>
          <div className="grid gap-4 md:grid-cols-2">
            <WeatherCard plan={plan} onRetry={onRetry} />
            <AttractionsCard plan={plan} onRetry={onRetry} />
            <div className="md:col-span-2">
              <RecommendationCard recommendation={plan.recommendation} />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
