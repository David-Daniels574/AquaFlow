import { Card } from "./ui/card"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from "recharts"

const data = [
  { month: "Jan", consumption: 1300 },
  { month: "Feb", consumption: 1250 },
  { month: "Mar", consumption: 1400 },
  { month: "Apr", consumption: 1350 },
  { month: "May", consumption: 1500 },
  { month: "Jun", consumption: 1600 },
  { month: "Jul", consumption: 1650 },
  { month: "Aug", consumption: 1700 },
  { month: "Sep", consumption: 1550 },
  { month: "Oct", consumption: 1450 },
  { month: "Nov", consumption: 1600 },
  { month: "Dec", consumption: 1750 },
]

export default function ConsumptionChart() {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Consumption</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "#6B7280" }} />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#6B7280" }}
              tickFormatter={(value) => `${value} KL`}
            />
            <Line type="monotone" dataKey="consumption" stroke="#2563EB" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center mt-4">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-600 rounded-full mr-2"></div>
          <span className="text-sm text-gray-600">Consumption</span>
        </div>
      </div>
    </Card>
  )
}
