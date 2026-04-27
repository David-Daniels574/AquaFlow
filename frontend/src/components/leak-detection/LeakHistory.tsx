import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, MapPin, Droplets } from "lucide-react";
import { motion } from "framer-motion";
import { useLeakDetection } from "@/hooks/useAPI";

export function LeakHistory() {
  const { data: leakData, isLoading, error } = useLeakDetection();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Leak Event History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, index) => (
              <div key={index} className="h-20 bg-gray-200 animate-pulse rounded-lg"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Leak Event History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-500">Failed to load leak history. Please try again later.</p>
        </CardContent>
      </Card>
    );
  }

  const leakEvents = leakData?.history || [];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Leak Event History</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {leakEvents.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">No leak events detected yet.</p>
        ) : (
          leakEvents.map((event, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="border rounded-lg p-4 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{new Date(event.date).toLocaleString()}</span>
                  </div>
                  <h3 className="font-semibold">{event.description}</h3>
                  <Badge 
                    variant={event.severity === "critical" ? "destructive" : 
                            event.severity === "moderate" ? "default" : "secondary"}
                    className="text-xs"
                  >
                    {event.severity} Severity
                  </Badge>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2 text-muted-foreground">
                  <Droplets className="h-4 w-4" />
                  <span>Est. Loss: {event.loss} Liters</span>
                </div>
                <div className="flex items-center space-x-2 text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  <span>Water System</span>
                </div>
              </div>
              
              <Button variant="link" className="p-0 h-auto text-primary">
                View Details
              </Button>
            </motion.div>
          ))
        )}
      </CardContent>
    </Card>
  );
}