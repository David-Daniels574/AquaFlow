export const tankerData = [
  {
    id: 1,
    name: "HydroServe Tankers",
    rating: 4.8,
    reviews: 1245,
    location: "Kotrund, Pune",
    capacities: ["500L", "1000L"],
    startPrice: 500,
    deliveryTime: "30-45 mins",
    image: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=200&fit=crop",
    badge: "500ML"
  },
  {
    id: 2,
    name: "AquaLogistics Solutions", 
    rating: 4.2,
    reviews: 892,
    location: "Hinjewadi, Pune",
    capacities: ["500L", "1200L", "1500L"],
    startPrice: 650,
    deliveryTime: "45-60 mins",
    image: "https://images.unsplash.com/photo-1597466765990-64ad1c35dafc?w=400&h=200&fit=crop",
    badge: "500ML"
  },
  {
    id: 3,
    name: "City Water Carriers",
    rating: 4.2,
    reviews: 732, 
    location: "Shivajinagar, Pune",
    capacities: ["800L", "1000L"],
    startPrice: 600,
    deliveryTime: "60-75 mins",
    image: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400&h=200&fit=crop",
    badge: "500ML"
  },
  {
    id: 4,
    name: "Reliable Aqua Supply",
    rating: 4.9,
    reviews: 1500,
    location: "Eames, Pune", 
    capacities: ["500L", "1000L"],
    startPrice: 550,
    deliveryTime: "25-40 mins",
    image: "https://images.unsplash.com/photo-1544896478-d5631f357f96?w=400&h=200&fit=crop",
    badge: "500ML"
  },
  {
    id: 5,
    name: "Ganga Water Services",
    rating: 4.4,
    reviews: 680,
    location: "Fangri-Chinchhad, Pune",
    capacities: ["500L", "800L"], 
    startPrice: 480,
    deliveryTime: "50-65 mins",
    image: "https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=400&h=200&fit=crop",
    badge: "500ML"
  },
  {
    id: 6,
    name: "Shanti Water Tankers",
    rating: 4.7,
    reviews: 1100,
    location: "Wakd, Pune",
    capacities: ["1000L", "1500L"],
    startPrice: 700,
    deliveryTime: "40-55 mins",
    image: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400&h=200&fit=crop",
    badge: "1000ML"
  }
];

export const leakEvents = [
  {
    id: 1,
    date: "October 26, 2024, 02:15 PM",
    title: "Unusual Overnight Flow",
    severity: "Critical Severity",
    loss: "500 Liters",
    location: "Main Pipeline",
  },
  {
    id: 2,
    date: "October 20, 2024, 09:30 AM", 
    title: "Continuous High Usage",
    severity: "Moderate Severity",
    loss: "250 Liters",
    location: "Kitchen Area",
  },
  {
    id: 3,
    date: "September 15, 2024, 01:00 PM",
    title: "Sporadic Small Drips",
    severity: "Minor Severity", 
    loss: "50 Liters",
    location: "Bathroom",
  },
  {
    id: 4,
    date: "September 01, 2024, 04:45 AM",
    title: "High Usage Alert",
    severity: "Moderate Severity",
    loss: "300 Liters",
    location: "Garden Area",
  },
];

export const recentReadings = [
  { date: "2024-07-28", meterReading: 12540, consumption: 160 },
  { date: "2024-07-27", meterReading: 12380, consumption: 180 },
  { date: "2024-07-26", meterReading: 12200, consumption: 175 },
  { date: "2024-07-25", meterReading: 12025, consumption: 190 },
  { date: "2024-07-24", meterReading: 11835, consumption: 155 },
  { date: "2024-07-23", meterReading: 11680, consumption: 210 },
];

export const chartData = {
  daily: [
    { day: 'Mon', consumption: 165 },
    { day: 'Wed', consumption: 185 },
    { day: 'Fri', consumption: 220 },
    { day: 'Sun', consumption: 190 },
  ],
  weekly: [
    { week: 'Week 2', consumption: 1050 },
    { week: 'Week 3', consumption: 1200 },
    { week: 'Week 4', consumption: 1100 },
    { week: 'Week 5', consumption: 1400 },
  ],
  monthly: [
    { month: 'Feb', consumption: 4200 },
    { month: 'Apr', consumption: 4500 }, 
    { month: 'Jun', consumption: 5100 },
  ]
};