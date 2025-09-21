import { Card } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from "recharts";
import { ChartContainer } from "@/components/ui/chart";
import { useSocietyDashboard } from "@/hooks/useAPI";

const chartConfig = {
  activeInitiatives: {
    label: "Active Initiatives",
    color: "hsl(210, 100%, 50%)",
  },
  pendingInitiatives: {
    label: "Pending Initiatives", 
    color: "hsl(38, 92%, 50%)",
  },
  completedInitiatives: {
    label: "Completed Initiatives",
    color: "hsl(0, 84%, 60%)",
  },
};

const COLORS = [
  "hsl(210, 100%, 50%)", // Blue for Active
  "hsl(38, 92%, 50%)",   // Orange for Pending
  "hsl(0, 84%, 60%)"     // Red for Completed
];

export function ConservationImpactChart() {
  const { data: dashboardData, isLoading, error } = useSocietyDashboard();

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-foreground">Conservation Impact</h3>
        </div>
        <div className="h-[200px] bg-gray-200 animate-pulse rounded"></div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-foreground">Conservation Impact</h3>
        </div>
        <p className="text-red-500">Failed to load conservation data.</p>
      </Card>
    );
  }

  const conservationImpactData = [
    { name: "Active Initiatives", value: dashboardData?.conservation_impact?.active || 0, color: "hsl(210, 100%, 50%)" },
    { name: "Pending Initiatives", value: dashboardData?.conservation_impact?.pending || 0, color: "hsl(38, 92%, 50%)" },
    { name: "Completed Initiatives", value: dashboardData?.conservation_impact?.completed || 0, color: "hsl(0, 84%, 60%)" }
  ];

  const renderCustomLabel = (entry: any) => {
    return `${entry.value}%`;
  };

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-foreground">Conservation Impact</h3>
      </div>
      <ChartContainer config={chartConfig} className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={conservationImpactData}
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
              label={renderCustomLabel}
              labelLine={false}
            >
              {conservationImpactData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Legend 
              verticalAlign="bottom" 
              height={36}
              formatter={(value, entry) => (
                <span style={{ color: entry.color, fontSize: '12px' }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </ChartContainer>
    </Card>
  );
}