// Dummy data for Conservation Hub Dashboard

export const conservationKPIs = {
  monthlyConsumption: {
    value: "1.7",
    unit: "KL",
    trend: "up" as const
  },
  tankersOrderedYTD: {
    value: "28",
    unit: "",
    trend: "up" as const
  },
  activeInitiatives: {
    value: "3",
    unit: "",
    trend: "stable" as const
  },
  waterSaved: {
    value: "15,000",
    unit: "L",
    trend: "up" as const
  }
};

export const monthlyConsumptionData = [
  { month: "Jan", consumption: 1500 },
  { month: "Feb", consumption: 1450 },
  { month: "Mar", consumption: 1520 },
  { month: "Apr", consumption: 1580 },
  { month: "May", consumption: 1620 },
  { month: "Jun", consumption: 1700 },
  { month: "Jul", consumption: 1650 },
  { month: "Aug", consumption: 1680 },
  { month: "Sep", consumption: 1590 },
  { month: "Oct", consumption: 1550 },
  { month: "Nov", consumption: 1600 },
  { month: "Dec", consumption: 1650 }
];

export const conservationImpactData = [
  { name: "Active Initiatives", value: 75, color: "hsl(210, 100%, 50%)" },
  { name: "Pending Initiatives", value: 15, color: "hsl(38, 92%, 50%)" },
  { name: "Completed Initiatives", value: 10, color: "hsl(0, 84%, 60%)" }
];

export const upcomingDeliveries = [
  {
    id: 1,
    supplier: "BlueDrop",
    date: "2024-07-25",
    time: "10:00 AM",
    volume: "10,000 L",
    status: "Scheduled"
  },
  {
    id: 2,
    supplier: "WaterGenie",
    date: "2024-07-26",
    time: "02:00 PM",
    volume: "5,000 L",
    status: "Scheduled"
  },
  {
    id: 3,
    supplier: "AquaDeliver",
    date: "2024-07-27",
    time: "09:00 AM",
    volume: "15,000 L",
    status: "Delayed"
  },
  {
    id: 4,
    supplier: "PureWater",
    date: "2024-07-28",
    time: "01:00 PM",
    volume: "8,000 L",
    status: "Scheduled"
  },
  {
    id: 5,
    supplier: "HydroLogistics",
    date: "2024-07-30",
    time: "11:00 AM",
    volume: "12,000 L",
    status: "Scheduled"
  }
];