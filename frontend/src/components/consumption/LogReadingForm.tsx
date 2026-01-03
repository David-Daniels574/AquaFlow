import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { useState } from "react";
import { motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";
// IMPORT YOUR API HELPER
import { consumptionAPI } from "@/services/api"; 

export function LogReadingForm() {
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [reading, setReading] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!reading || !date) {
      toast({
        title: "Error",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }

    const readingValue = parseFloat(reading);
    if (isNaN(readingValue) || readingValue <= 0) {
      toast({
        title: "Error",
        description: "Please enter a valid positive number",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    
    try {
      // USE THE HELPER FUNCTION
      // FIX: Replace 'Z' with '+00:00' to prevent Python errors
      await consumptionAPI.logReading({
        reading: readingValue,
        timestamp: date.toISOString().replace('Z', '+00:00')
      });
      
      toast({
        title: "Success",
        description: "Water reading logged successfully",
      });
      
      setReading("");
    } catch (error) {
      console.error("Error logging reading:", error);
      toast({
        title: "Error",
        description: "Failed to log reading. Check your connection.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
      <Card>
        <CardHeader>
          <CardTitle>Log New Reading</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="meter-reading">Current Meter Reading (Litres)</Label>
              <Input
                id="meter-reading"
                placeholder="e.g., 12345"
                value={reading}
                onChange={(e) => setReading(e.target.value)}
                type="number"
                min="0"
                step="0.01"
                required
              />
            </div>
            
            <div className="space-y-2 mt-4">
              <Label>Date of Reading</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start text-left font-normal"
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {date ? format(date, "yyyy-MM-dd") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={setDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
            
            <Button 
              type="submit" 
              className="w-full bg-primary hover:bg-primary-hover mt-4"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Saving..." : "Save Reading"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}