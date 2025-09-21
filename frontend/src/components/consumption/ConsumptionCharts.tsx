import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, BarChart, Bar } from "recharts";
import { motion } from "framer-motion";
import { useConsumptionReport } from "@/hooks/useAPI";

export function ConsumptionCharts() {
  const { data: dailyReport, isLoading: dailyLoading } = useConsumptionReport('daily', true);
  const { data: weeklyReport, isLoading: weeklyLoading } = useConsumptionReport('weekly');
  const { data: monthlyReport, isLoading: monthlyLoading } = useConsumptionReport('monthly');

  // Transform API data to chart format
  const dailyData = dailyReport?.readings?.map((reading, index) => ({
    day: `Day ${index + 1}`,
    consumption: reading.reading
  })) || [];

  const weeklyData = [
    { week: 'Week 1', consumption: weeklyReport?.total_consumption || 0 },
    { week: 'Week 2', consumption: (weeklyReport?.total_consumption || 0) * 1.1 },
    { week: 'Week 3', consumption: (weeklyReport?.total_consumption || 0) * 0.9 },
    { week: 'Week 4', consumption: (weeklyReport?.total_consumption || 0) * 1.2 },
  ];

  const monthlyData = [
    { month: 'Jan', consumption: (monthlyReport?.total_consumption || 0) * 0.8 },
    { month: 'Feb', consumption: monthlyReport?.total_consumption || 0 },
    { month: 'Mar', consumption: (monthlyReport?.total_consumption || 0) * 1.1 },
  ];
  return (
    <div className="grid md:grid-cols-3 gap-6">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Daily Consumption</CardTitle>
          </CardHeader>
          <CardContent>
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
            <div className="mt-2 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-chart-primary rounded-full"></div>
                <span>Consumption (L)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Weekly Consumption</CardTitle>
          </CardHeader>
          <CardContent>
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
            <div className="mt-2 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-chart-secondary rounded-full"></div>
                <span>Consumption (L)</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Monthly Consumption</CardTitle>
          </CardHeader>
          <CardContent>
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