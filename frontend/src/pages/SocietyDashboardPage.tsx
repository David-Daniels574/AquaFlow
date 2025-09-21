import { motion } from "framer-motion";
import { DropletIcon, Truck, Target, Leaf } from "lucide-react";
import { KPICard } from "@/components/conservation/KPICard";
import { ConsumptionChart } from "@/components/conservation/ConsumptionChart";
import { ConservationImpactChart } from "@/components/conservation/ConservationImpactChart";
import { UpcomingDeliveries } from "@/components/conservation/UpcomingDeliveries";
import { CommunicationHub } from "@/components/conservation/CommunicationHub";
import { useSocietyDashboard } from "@/hooks/useAPI";

export default function SocietyDashboardPage() {
  const { data: dashboardData, isLoading, error } = useSocietyDashboard();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Society Management Dashboard</h1>
          <p className="text-muted-foreground">Loading dashboard data...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, index) => (
            <div key={index} className="h-32 bg-gray-200 animate-pulse rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Society Management Dashboard</h1>
          <p className="text-red-500">Failed to load dashboard data. Please try again later.</p>
        </div>
      </div>
    );
  }

  // Calculate current month consumption from monthly data
  const currentMonth = new Date().getMonth() + 1;
  const currentMonthConsumption = dashboardData?.monthly_consumption?.[currentMonth] || 0;
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">Society Management Dashboard</h1>
        <p className="text-muted-foreground">
          Centralized platform for managing water resources and communication within your society.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Monthly Consumption"
          value={(currentMonthConsumption / 1000).toFixed(1)}
          unit="KL"
          trend="up"
          icon={DropletIcon}
        />
        <KPICard
          title="Tankers Ordered YTD"
          value={dashboardData?.tankers_ordered_ytd?.toString() || "0"}
          unit=""
          trend="up"
          icon={Truck}
        />
        <KPICard
          title="Active Initiatives"
          value={dashboardData?.active_initiatives?.toString() || "0"}
          unit=""
          trend="stable"
          icon={Target}
        />
        <KPICard
          title="Water Saved (Approx)"
          value={(dashboardData?.water_saved || 0).toLocaleString()}
          unit="L"
          trend="up"
          icon={Leaf}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Charts and Table */}
        <div className="lg:col-span-2 space-y-6">
          <ConsumptionChart />
          <UpcomingDeliveries />
        </div>

        {/* Right Column - Impact Chart and Communication */}
        <div className="space-y-6">
          <ConservationImpactChart />
          <CommunicationHub />
        </div>
      </div>
    </motion.div>
  );
}