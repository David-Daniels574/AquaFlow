import { Droplet, Target, Award } from "lucide-react"

export default function ProgressSection() {
  const stats = [
    {
      icon: Droplet,
      title: "Water Saved This Month",
      value: "5000",
      unit: "Liters",
      color: "text-blue-600",
    },
    {
      icon: Target,
      title: "Active Challenges",
      value: "3",
      unit: "",
      color: "text-blue-600",
    },
    {
      icon: Award,
      title: "Eco-Points Earned",
      value: "1500",
      unit: "",
      color: "text-blue-600",
    },
  ]

  return (
    <section className="mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Conservation Progress</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="bg-white rounded-lg p-6 text-center shadow-sm border border-gray-200">
              <Icon className={`w-12 h-12 mx-auto mb-4 ${stat.color}`} />
              <h3 className="text-gray-600 text-sm font-medium mb-2">{stat.title}</h3>
              <div className="flex items-baseline justify-center">
                <span className={`text-3xl font-bold ${stat.color}`}>{stat.value}</span>
                {stat.unit && <span className={`text-lg ml-1 ${stat.color}`}>{stat.unit}</span>}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
