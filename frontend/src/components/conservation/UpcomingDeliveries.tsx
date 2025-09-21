import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSocietyDashboard } from "@/hooks/useAPI";

export function UpcomingDeliveries() {
  const { data: dashboardData, isLoading, error } = useSocietyDashboard();

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "scheduled":
      case "pending":
        return <Badge variant="secondary" className="bg-status-success/10 text-status-success hover:bg-status-success/20">Scheduled</Badge>;
      case "delayed":
        return <Badge variant="destructive">Delayed</Badge>;
      case "en_route":
        return <Badge variant="default">En Route</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-foreground">Upcoming Tanker Deliveries</h3>
        </div>
        <div className="space-y-2">
          {[...Array(3)].map((_, index) => (
            <div key={index} className="h-12 bg-gray-200 animate-pulse rounded"></div>
          ))}
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-foreground">Upcoming Tanker Deliveries</h3>
        </div>
        <p className="text-red-500">Failed to load delivery data.</p>
      </Card>
    );
  }

  const deliveries = dashboardData?.scheduled_deliveries || [];

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground">Upcoming Tanker Deliveries</h3>
      </div>
      <div className="overflow-hidden">
        {deliveries.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">No upcoming deliveries scheduled.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs font-medium">Supplier</TableHead>
                <TableHead className="text-xs font-medium">Date</TableHead>
                <TableHead className="text-xs font-medium">Time</TableHead>
                <TableHead className="text-xs font-medium">Volume</TableHead>
                <TableHead className="text-xs font-medium">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {deliveries.map((delivery, index) => (
                <TableRow key={index}>
                  <TableCell className="text-sm font-medium">{delivery.supplier}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{delivery.date}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{delivery.time}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{delivery.volume}L</TableCell>
                  <TableCell>{getStatusBadge(delivery.status)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
         </div>
    </Card>
  );
}