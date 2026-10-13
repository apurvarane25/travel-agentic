const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchTravelPlan({ city, startDate, endDate }) {
    const url = `${API_URL}/api/travel-plan`;
    console.log("Calling:", url);

    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, start_date: startDate, end_date: endDate }),
    });

    if (!res.ok) {
        const body = await res.text();
        throw new Error(`${res.status} from ${url}: ${body.slice(0, 200)}`);
    }

    const data = await res.json();
    if (data.error) throw new Error(data.error);

    return data.recommendation;
}