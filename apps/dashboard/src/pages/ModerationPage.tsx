import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAccount } from "../api/accounts";
import { observationSummary } from "../api/observations";
import { ApiRequestError, fetchApi, type Page } from "../api/transport";
import OperatorAccess from "../components/auth/OperatorAccess";
import OperatorHeader from "../components/OperatorHeader";
import { Button } from "../components/ui";
interface Report {
  protocol_id?: string;
  observation?: Record<string,unknown>;
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
    queryFn: async () => {
      const legacy = await fetchApi<Page<Report>>("/api/v1/moderation/reports?limit=100");
      try {
        const current = await fetchApi<Page<Report>>("/api/v2/moderation/observations?limit=100");
        return {...legacy, total:legacy.total+current.total, items:[...legacy.items,...current.items].sort((a,b)=>a.observed_at.localeCompare(b.observed_at))};
      } catch(e) { if(e instanceof ApiRequestError && e.status===404) return legacy; throw e; }
    },
    enabled: allowed,
    retry: false,
  });
  async function review(report: Report, status: "approved" | "rejected") {
    const id=report.id;
    setBusy(id);
    setError("");
    try {
      await fetchApi(`${report.observation ? "/api/v2/observations" : "/api/v1/reports"}/${id}/moderation`, {
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
    <div className="min-h-full">
    <OperatorHeader context="Report review" />
    <main className="mx-auto max-w-4xl space-y-6 px-4 py-6 sm:px-6">
      <h1 className="text-2xl font-semibold">Citizen report review</h1>
      <OperatorAccess />
      {!allowed && (
        <p>
          An approved reviewer invitation and operator sign-in with MFA are
          required.
        </p>
      )}
      {(error || queue.error) && (
        <div role="alert" className="rounded border border-destructive p-4 text-sm">
          <p>{error || queue.error?.message}</p>
          {queue.error && <Button className="mt-3 min-h-11" onClick={() => void queue.refetch()}>Retry reports</Button>}
        </div>
      )}
      {queue.isFetching && <p role="status">Loading reports…</p>}
      {queue.data && (
        <p>
          {queue.data.total} reports awaiting review. Showing up to 200, oldest
          first.
        </p>
      )}
      {queue.data?.total === 0 && <p role="status" className="text-sm text-muted-foreground">No reports are awaiting review.</p>}
      {queue.data?.items.map((report) => (
        <article key={report.id} className="space-y-3 rounded-lg border border-border bg-card p-4 [overflow-wrap:anywhere]">
          <h2 className="font-semibold">
            {report.observation ? "Citizen observation" : `Legacy ${report.category}`} · {new Date(report.observed_at).toLocaleString()}
          </h2>
          <p>
            {report.observation ? observationSummary(report.observation) : report.condition ??
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
              className="mt-2 block min-h-24 w-full rounded-md border border-input bg-background p-3 text-sm"
              maxLength={2000}
              value={reason[report.id] ?? ""}
              onChange={(e) =>
                setReason({ ...reason, [report.id]: e.target.value })
              }
            />
          </label>
          <div className="flex flex-wrap gap-3">
            {(["approved", "rejected"] as const).map((status) => (
              <Button
                key={status}
                variant={status === "approved" ? "primary" : "danger"}
                className="min-h-11"
                disabled={busy !== null || !reason[report.id]?.trim()}
                onClick={() => review(report, status)}
              >
                {status === "approved" ? "Approve public summary" : "Reject"}
              </Button>
            ))}
          </div>
          <p className="text-sm">
            Approval publishes only the structured reading and rounded location.
            Notes and photos remain private.
          </p>
        </article>
      ))}
    </main>
    </div>
  );
}
