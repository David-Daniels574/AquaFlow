import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar } from "recharts";
import { motion } from "framer-motion";
import { useConsumptionReport } from "@/hooks/useAPI";

export function ConsumptionCharts() {
  // 1. Fetch 7 days of data for the "Daily" chart
  const { data: dailyReport, isLoading: dailyLoading } = useConsumptionReport('weekly', true);
  
  // 2. Fetch 30 days of data to group for both "Weekly" and "Monthly" charts
  const { data: monthlyReport, isLoading: monthlyLoading } = useConsumptionReport('monthly', true);

  // --- Processing Functions ---

  // Process Daily: Format 7 days of daily breakdowns
  const processDailyData = (report: any) => {
    if (!report?.daily_breakdown) return [];
    return report.daily_breakdown.map((item: any) => {
      const d = new Date(item.date);
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return {
        day: `${d.getDate()} ${monthNames[d.getMonth()]}`, // e.g. "15 Mar"
        consumption: Math.round(item.usage * 10) / 10
      };
    });
  };

  // Process Weekly: Group 30 days into chunks of weeks and SUM them
  const processWeeklyData = (report: any) => {
    if (!report?.daily_breakdown) return [];
    const weeks: { [key: string]: number } = {};
    
    report.daily_breakdown.forEach((item: any) => {
      const d = new Date(item.date);
      const startOfWeek = new Date(d);
      startOfWeek.setDate(d.getDate() - d.getDay()); // Align to Sunday
      const weekKey = startOfWeek.toISOString().split('T')[0];
      
      weeks[weekKey] = (weeks[weekKey] || 0) + item.usage;
    });

    return Object.keys(weeks).sort().map((key, index) => ({
      week: `Week ${index + 1}`,
      consumption: Math.round(weeks[key] * 10) / 10
    }));
  };

  // Process Monthly: Group 30 days by Month name and SUM them
  const processMonthlyData = (report: any) => {
    if (!report?.daily_breakdown) return [];
    const months: { [key: string]: number } = {};
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    report.daily_breakdown.forEach((item: any) => {
      const d = new Date(item.date);
      // Group by Year-Month to keep it unique
      const monthKey = `${d.getFullYear()}-${d.getMonth()}`;
      months[monthKey] = (months[monthKey] || 0) + item.usage;
    });

    return Object.keys(months).sort().map((key) => {
      const [, mIndex] = key.split('-');
      return {
        month: monthNames[parseInt(mIndex)],
        consumption: Math.round(months[key] * 10) / 10
      };
    });
  };

  const dailyData = processDailyData(dailyReport);
  const weeklyData = processWeeklyData(monthlyReport);
  const monthlyData = processMonthlyData(monthlyReport);

  return (
    <div className="grid md:grid-cols-3 gap-6">
      {/* DAILY CHART */}
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Daily Consumption</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyLoading ? (
              <div className="h-[200px] flex items-center justify-center">
                <div className="text-muted-foreground">Loading daily data...</div>
              </div>
            ) : dailyData.length === 0 ? (
              <div className="h-[200px] flex items-center justify-center">
                <div className="text-muted-foreground">No daily data available</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Line 
                    type="monotone" 
                    dataKey="consumption" 
                    stroke="hsl(var(--chart-primary))" 
                    strokeWidth={2}
                    dot={{ fill: "hsl(var(--chart-primary))", strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
            <div className="mt-2 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-chart-primary rounded-full"></div>
                <span>Consumption (L)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* WEEKLY CHART */}
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Weekly Consumption</CardTitle>
          </CardHeader>
          <CardContent>
            {monthlyLoading ? (
              <div className="h-[200px] flex items-center justify-center">
                <div className="text-muted-foreground">Loading weekly data...</div>
              </div>
            ) : weeklyData.length === 0 ? (
              <div className="h-[200px] flex items-center justify-center">
                <div className="text-muted-foreground">No weekly data available</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Bar 
                    dataKey="consumption" 
                    fill="hsl(var(--chart-secondary))"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
            <div className="mt-2 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-chart-secondary rounded-full"></div>
                <span>Consumption (L)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* MONTHLY CHART */}
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Monthly Consumption</CardTitle>
          </CardHeader>
          <CardContent>
            {monthlyLoading ? (
              <div className="h-[200px] flex items-center justify-center">
                <div className="text-muted-foreground">Loading monthly data...</div>
              </div>
            ) : monthlyData.length === 0 ? (
              <div className="h-[200px] flex items-center justify-center">
                <div className="text-muted-foreground">No monthly data available</div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Bar 
                    dataKey="consumption" 
                    fill="hsl(var(--foreground))"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
            <div className="mt-2 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-foreground rounded-full"></div>
                <span>Consumption (L)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}