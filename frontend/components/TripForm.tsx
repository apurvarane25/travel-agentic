"use client";
import { useState, type FormEvent } from "react";
import { ApiError, type TravelRequest, type TripField } from "@/lib/travelApi";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = {
  onSubmit: (request: TravelRequest) => void;
  loading: boolean;
  error: ApiError | null;
  initialValues?: Partial<TravelRequest>;
};

function getLocalToday() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function TripForm({ onSubmit, loading, error, initialValues }: Props) {
  const [city, setCity] = useState(initialValues?.city ?? "");
  const [startDate, setStartDate] = useState(initialValues?.start_date ?? "");
  const [endDate, setEndDate] = useState(initialValues?.end_date ?? "");
  const today = getLocalToday();
  const fieldErrors = error?.status === 422 ? error.fields : {};
  const formError = error?.status === 422 ? error.message : null;

  function fieldError(field: TripField) {
    return fieldErrors[field];
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onSubmit({ city, start_date: startDate, end_date: endDate || null });
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-3">
        <Field>
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            name="city"
            autoComplete="address-level2"
            value={city}
            onChange={(event) => setCity(event.target.value)}
            aria-invalid={Boolean(fieldError("city"))}
            aria-describedby={fieldError("city") ? "city-error" : undefined}
            required
          />
          <FieldError id="city-error">{fieldError("city")}</FieldError>
        </Field>
        <Field>
          <Label htmlFor="start_date">Start date</Label>
          <Input
            id="start_date"
            name="start_date"
            type="date"
            value={startDate}
            min={today}
            onChange={(event) => setStartDate(event.target.value)}
            aria-invalid={Boolean(fieldError("start_date"))}
            aria-describedby={fieldError("start_date") ? "start-date-error" : undefined}
            required
          />
          <FieldError id="start-date-error">{fieldError("start_date")}</FieldError>
        </Field>
        <Field>
          <Label htmlFor="end_date">End date <span className="font-normal text-muted-foreground">(optional)</span></Label>
          <Input
            id="end_date"
            name="end_date"
            type="date"
            value={endDate}
            min={startDate || today}
            onChange={(event) => setEndDate(event.target.value)}
            aria-invalid={Boolean(fieldError("end_date"))}
            aria-describedby={fieldError("end_date") ? "end-date-error" : "end-date-hint"}
          />
          <FieldDescription id="end-date-hint">Leave empty for a one-day trip.</FieldDescription>
          <FieldError id="end-date-error">{fieldError("end_date")}</FieldError>
        </Field>
      </div>
      {formError && <p className="text-sm text-destructive" role="alert">{formError}</p>}
      <Button type="submit" disabled={loading}>
        {loading ? "Planning…" : "Plan my trip"}
      </Button>
    </form>
  );
}
