import { Card } from "./ui/card"
import { TrendingUp, Truck, Target, Droplets } from "lucide-react"

export default function SocietyMetrics() {
  const metrics = [
    {
      title: "Monthly Consumption",
      value: "1.7 KL",
      icon: TrendingUp,
      trend: "up",
    },
    {
      title: "Tankers Ordered YTD",
      value: "28",
      icon: Truck,
      trend: "up",
    },
    {
      title: "Active Initiatives",
      value: "3",
      icon: Target,
      trend: "neutral",
    },
    {
      title: "Water Saved (Approx)",
      value: "15,000 L",
      icon: Droplets,
      trend: "up",
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {metrics.map((metric, index) => {
        const Icon = metric.icon
        return (
          <Card key={index} className="p-6">
            <div className="flex items-center justify-between mb-2">
              <Icon className="h-5 w-5 text-blue-600" />
              {metric.trend === "up" && <TrendingUp className="h-4 w-4 text-green-500" />}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-600">{metric.title}</p>
              <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
