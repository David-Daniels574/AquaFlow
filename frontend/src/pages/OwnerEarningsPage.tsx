import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useOwnerEarnings } from "@/hooks/useAPI";

export default function OwnerEarningsPage() {
  const { data, isLoading, error } = useOwnerEarnings();

  if (isLoading) {
    return <div className="text-muted-foreground">Loading earnings...</div>;
  }

  if (error) {
    return <div className="text-red-500">Failed to load earnings.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl p-6 bg-gradient-to-r from-primary/15 to-primary/5">
        <h1 className="text-2xl font-bold">Earnings and Analytics</h1>
        <p className="text-muted-foreground">Revenue, order completion, and tanker-wise performance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Earnings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">Rs {data?.total_earnings ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Completed Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{data?.completed_orders ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monthly Revenue</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {!data?.monthly?.length ? (
            <p className="text-sm text-muted-foreground">No completed deliveries yet.</p>
          ) : (
            data.monthly.map((m) => (
              <div key={m.month} className="rounded-md border p-3 flex items-center justify-between">
                <span>{m.month}</span>
                <span className="font-semibold">Rs {m.amount}</span>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tanker-wise Earnings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {!data?.by_tanker?.length ? (
            <p className="text-sm text-muted-foreground">No tanker earnings to show.</p>
          ) : (
            data.by_tanker.map((t) => (
              <div key={t.tanker_id} className="rounded-md border p-3 flex items-center justify-between">
                <span>{t.vehicle_number}</span>
                <span className="font-semibold">Rs {t.amount}</span>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
