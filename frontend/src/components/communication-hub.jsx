import { Card } from "./ui/card"
import { Button } from "./ui/button"
import { Textarea } from "./ui/textarea"
import { Send } from "lucide-react"

export default function CommunicationHub() {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Communication Hub</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Broadcast Message to Residents</label>
          <Textarea placeholder="Type your announcement or water schedule here..." className="min-h-32 resize-none" />
        </div>
        <Button className="w-full bg-blue-600 hover:bg-blue-700">
          <Send className="w-4 h-4 mr-2" />
          Send Notification
        </Button>
      </div>
    </Card>
  )
}
