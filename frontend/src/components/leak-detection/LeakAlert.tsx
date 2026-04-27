import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

export function LeakAlert() {
  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
    >
      <Card className="border-alert-critical bg-red-50">
        <CardContent className="flex items-center space-x-3 p-4">
          <AlertTriangle className="h-6 w-6 text-alert-critical" />
          <span className="text-alert-critical font-medium text-lg">
            Potential Leak Detected!
          </span>
        </CardContent>
      </Card>
    </motion.div>
  );
}