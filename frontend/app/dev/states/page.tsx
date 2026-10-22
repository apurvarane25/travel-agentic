import { notFound } from "next/navigation";
import StatesShowcase from "./StatesShowcase";

export default function DevelopmentStatesPage() {
    if (process.env.NODE_ENV === "production") notFound();

    return <StatesShowcase />;
}