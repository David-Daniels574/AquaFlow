import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useOwnerDashboard } from "@/hooks/useAPI";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}

export default function OwnerDashboardPage() {
  const { data, isLoading, error } = useOwnerDashboard();

  if (isLoading) {
    return <div className="text-muted-foreground">Loading owner dashboard...</div>;
  }

  if (error) {
    return <div className="text-red-500">Failed to load owner dashboard.</div>;
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="rounded-xl p-8 bg-gradient-to-r from-primary/15 to-primary/5">
        <h1 className="text-3xl font-bold">Tanker Owner Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Manage your fleet, listings, bookings, and earnings from one place.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Tankers" value={data?.total_tankers ?? 0} />
        <StatCard title="Active Bookings" value={data?.active_bookings ?? 0} />
        <StatCard title="This Month Earnings" value={`Rs ${data?.this_month_earnings ?? 0}`} />
        <StatCard title="Average Rating" value={data?.average_rating ?? 0} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Add New Tanker</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">Create a new listing with pricing and service areas.</p>
            <Button asChild>
              <Link to="/owner-dashboard/tankers">Open Tankers</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pending Bookings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">You currently have {data?.pending_bookings ?? 0} pending requests.</p>
            <Button asChild variant="secondary">
              <Link to="/owner-dashboard/bookings">Review Bookings</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Earnings and Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">Track payouts, trends, and tanker-wise revenue.</p>
            <Button asChild variant="outline">
              <Link to="/owner-dashboard/earnings">View Earnings</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {!data?.recent_activity?.length ? (
            <p className="text-sm text-muted-foreground">No recent activity.</p>
          ) : (
            data.recent_activity.map((a) => (
              <div key={a.booking_id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="font-medium">Booking #{a.booking_id}</p>
                  <p className="text-sm text-muted-foreground">Status: {a.status}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">Rs {a.total_amount}</p>
                  <p className="text-xs text-muted-foreground">Qty: {a.quantity}L</p>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
