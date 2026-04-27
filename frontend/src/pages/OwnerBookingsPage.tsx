import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useOwnerBookings, useOwnerUpdateBookingStatus } from "@/hooks/useAPI";
import { useToast } from "@/hooks/use-toast";

const tabs = ["all", "pending", "confirmed", "in_transit", "completed", "cancelled"] as const;
type Tab = (typeof tabs)[number];

export default function OwnerBookingsPage() {
  const [tab, setTab] = useState<Tab>("all");
  const { toast } = useToast();
  const { data: bookings, isLoading } = useOwnerBookings();
  const updateMutation = useOwnerUpdateBookingStatus();

  const filtered = useMemo(() => {
    if (!bookings) return [];
    if (tab === "all") return bookings;
    return bookings.filter((b) => b.status === tab);
  }, [bookings, tab]);

  const onUpdate = async (
    bookingId: number,
    status: "pending" | "confirmed" | "in_transit" | "completed" | "cancelled"
  ) => {
    try {
      await updateMutation.mutateAsync({ bookingId, status });
      toast({ title: "Booking updated", description: `Status changed to ${status}.` });
    } catch (error: any) {
      toast({ title: "Update failed", description: error.message, variant: "destructive" });
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl p-6 bg-gradient-to-r from-primary/15 to-primary/5">
        <h1 className="text-2xl font-bold">Bookings Management</h1>
        <p className="text-muted-foreground">Accept, reject, and complete customer tanker requests.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button key={t} variant={tab === t ? "default" : "outline"} onClick={() => setTab(t)}>
            {t === "all" ? "All" : t.replace("_", " ")}
          </Button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Orders</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoading ? (
            <p className="text-muted-foreground">Loading bookings...</p>
          ) : !filtered.length ? (
            <p className="text-muted-foreground">No bookings in this state.</p>
          ) : (
            filtered.map((booking) => (
              <div key={booking.id} className="rounded-lg border p-4 space-y-2">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                  <div>
                    <p className="font-semibold">Booking #{booking.id} • {booking.tanker_vehicle_number}</p>
                    <p className="text-sm text-muted-foreground">
                      Customer: {booking.customer.username} ({booking.customer.email})
                    </p>
                  </div>
                  <p className="font-medium">Rs {booking.total_amount}</p>
                </div>

                <p className="text-sm text-muted-foreground">Address: {booking.delivery_address || "Not provided"}</p>
                <p className="text-sm text-muted-foreground">Quantity: {booking.quantity}L • Status: {booking.status}</p>

                <div className="flex flex-wrap gap-2 pt-2">
                  <Button size="sm" variant="outline" onClick={() => onUpdate(booking.id, "confirmed")}>Accept</Button>
                  <Button size="sm" variant="outline" onClick={() => onUpdate(booking.id, "cancelled")}>Reject</Button>
                  <Button size="sm" variant="outline" onClick={() => onUpdate(booking.id, "in_transit")}>Mark In Transit</Button>
                  <Button size="sm" onClick={() => onUpdate(booking.id, "completed")}>Mark Delivered</Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
