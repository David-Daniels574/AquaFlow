import { Card } from "./ui/card"
import { Badge } from "./ui/badge"

const deliveries = [
  {
    supplier: "BlueDrop",
    date: "2024-07-25",
    time: "10:00 AM",
    volume: "10,000 L",
    status: "Scheduled",
  },
  {
    supplier: "WaterGenie",
    date: "2024-07-28",
    time: "02:00 PM",
    volume: "5,000 L",
    status: "Scheduled",
  },
  {
    supplier: "AquaDeliver",
    date: "2024-08-01",
    time: "09:00 AM",
    volume: "15,000 L",
    status: "Delayed",
  },
  {
    supplier: "PureWater",
    date: "2024-08-05",
    time: "01:00 PM",
    volume: "8,000 L",
    status: "Scheduled",
  },
  {
    supplier: "HydroLogistics",
    date: "2024-08-08",
    time: "11:00 AM",
    volume: "12,000 L",
    status: "Scheduled",
  },
]

export default function TankerDeliveries() {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Tanker Deliveries</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 text-sm font-medium text-gray-600">Supplier</th>
              <th className="text-left py-2 text-sm font-medium text-gray-600">Date</th>
              <th className="text-left py-2 text-sm font-medium text-gray-600">Time</th>
              <th className="text-left py-2 text-sm font-medium text-gray-600">Volume</th>
              <th className="text-left py-2 text-sm font-medium text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {deliveries.map((delivery, index) => (
              <tr key={index} className="border-b border-gray-100">
                <td className="py-3 text-sm font-medium text-gray-900">{delivery.supplier}</td>
                <td className="py-3 text-sm text-gray-600">{delivery.date}</td>
                <td className="py-3 text-sm text-gray-600">{delivery.time}</td>
                <td className="py-3 text-sm text-gray-600">{delivery.volume}</td>
                <td className="py-3">
                  <Badge
                    variant={delivery.status === "Delayed" ? "destructive" : "default"}
                    className={
                      delivery.status === "Delayed" ? "bg-orange-100 text-orange-800" : "bg-blue-100 text-blue-800"
                    }
                  >
                    {delivery.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
