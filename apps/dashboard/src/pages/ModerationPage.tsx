import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAccount } from "../api/accounts";
import { fetchApi, type Page } from "../api/transport";
import OperatorAccess from "../components/auth/OperatorAccess";
interface Report {
  id: string;
  category: string;
  observed_at: string;
  note: string | null;
  latitude: number;
  longitude: number;
  media_id: string | null;
  condition: string | null;
  reading_value: number | null;
  reading_unit: string | null;
}
export default function ModerationPage() {
  const { data: account } = useAccount();
  const queryClient = useQueryClient();
  const [reason, setReason] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const allowed = account?.capabilities.includes("report:review") ?? false;
  const queue = useQuery({
    queryKey: ["moderation"],
    queryFn: () =>
      fetchApi<Page<Report>>("/api/v1/moderation/reports?limit=100"),
    enabled: allowed,
    retry: false,
  });
  async function review(id: string, status: "approved" | "rejected") {
    setBusy(id);
    setError("");
    try {
      await fetchApi(`/api/v1/reports/${id}/moderation`, {
        method: "POST",
        body: JSON.stringify({ status, reason: reason[id]?.trim() }),
      });
      await queryClient.invalidateQueries({ queryKey: ["moderation"] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed");
    } finally {
      setBusy(null);
    }
  }
  return (
    <main className="mx-auto max-w-4xl space-y-6 p-6">
      <Link to="/dashboard" className="underline">
        Return to monitoring
      </Link>
      <h1 className="text-2xl font-semibold">Citizen report review</h1>
      <OperatorAccess />
      {!allowed && (
        <p>
          An approved reviewer invitation and operator sign-in with MFA are
          required.
        </p>
      )}
      {(error || queue.error) && (
        <p role="alert">{error || queue.error?.message}</p>
      )}
      {queue.isFetching && <p role="status">Loading reports…</p>}
      {queue.data && (
        <p>
          {queue.data.total} reports awaiting review. Showing up to 100, oldest
          first.
        </p>
      )}
      {queue.data?.items.map((report) => (
        <article key={report.id} className="space-y-3 rounded border p-4">
          <h2 className="font-semibold">
            {report.category} · {new Date(report.observed_at).toLocaleString()}
          </h2>
          <p>
            {report.condition ??
              `${report.reading_value} ${report.reading_unit}`}
          </p>
          <p>
            Private location: {report.latitude}, {report.longitude}
          </p>
          {report.note && <p className="whitespace-pre-wrap">{report.note}</p>}
          {report.media_id && (
            <a
              className="underline"
              href={`/api/v1/media/${report.media_id}`}
              target="_blank"
              rel="noreferrer"
            >
              View private photo
            </a>
          )}
          <label className="block">
            Review reason
            <textarea
              className="mt-1 block w-full rounded border p-2"
              maxLength={2000}
              value={reason[report.id] ?? ""}
              onChange={(e) =>
                setReason({ ...reason, [report.id]: e.target.value })
              }
            />
          </label>
          <div className="flex gap-4">
            {(["approved", "rejected"] as const).map((status) => (
              <button
                key={status}
                className="rounded border px-4 py-2 disabled:opacity-40"
                disabled={busy !== null || !reason[report.id]?.trim()}
                onClick={() => review(report.id, status)}
              >
                {status === "approved" ? "Approve public summary" : "Reject"}
              </button>
            ))}
          </div>
          <p className="text-sm">
            Approval publishes only the structured reading and rounded location.
            Notes and photos remain private.
          </p>
        </article>
      ))}
    </main>
  );
}
