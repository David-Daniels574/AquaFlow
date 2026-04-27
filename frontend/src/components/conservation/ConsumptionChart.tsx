import { Card } from "@/components/ui/card";
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { useSocietyDashboard } from "@/hooks/useAPI";

const chartConfig = {
  consumption: {
    label: "Consumption",
    color: "hsl(var(--chart-primary))",
  },
};

export function ConsumptionChart() {
  const { data: dashboardData, isLoading, error } = useSocietyDashboard();

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-foreground">Monthly Consumption</h3>
        </div>
        <div className="h-[200px] bg-gray-200 animate-pulse rounded"></div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-foreground">Monthly Consumption</h3>
        </div>
        <p className="text-red-500">Failed to load consumption data.</p>
      </Card>
    );
  }

  // Transform monthly consumption data to chart format
  const monthlyConsumptionData = Object.entries(dashboardData?.monthly_consumption || {}).map(([month, consumption]) => ({
    month: new Date(2024, parseInt(month) - 1).toLocaleDateString('en-US', { month: 'short' }),
    consumption: consumption || 0
  }));
  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground">Monthly Consumption</h3>
      </div>
      <ChartContainer config={chartConfig} className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={monthlyConsumptionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="month" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line
              type="monotone"
              dataKey="consumption"
              stroke="var(--color-consumption)"
              strokeWidth={2}
              dot={{ fill: "var(--color-consumption)", strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: "var(--color-consumption)", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartContainer>
    </Card>
  );
}