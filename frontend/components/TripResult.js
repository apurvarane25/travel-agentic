import ReactMarkdown from "react-markdown";

export default function TripResult({ result, error }) {
    if (error) return <p style={{ color: "red" }}>Error: {error}</p>;
    if (!result) return null;
    return <ReactMarkdown>{result}</ReactMarkdown>;
}