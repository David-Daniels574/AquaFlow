import { useState } from "react"
import Header from "../components/header"
import Sidebar from "../components/sidebar"
import SocietyMetrics from "../components/society-metrics"
import ConsumptionChart from "../components/consumption-chart"
import ConservationChart from "../components/conservation-chart"
import TankerDeliveries from "../components/tanker-deliveries"
import CommunicationHub from "../components/communication-hub"
import Footer from "../components/footer"

export default function SocietyDashboard({ currentPage, onPageChange }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      <div className="flex">
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          currentPage={currentPage}
          onPageChange={onPageChange}
        />
        <main className="flex-1 p-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Society Management Dashboard</h1>
            <p className="text-gray-600">
              Centralized platform for managing water resources and communication within your society.
            </p>
          </div>

          <SocietyMetrics />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <ConsumptionChart />
            <ConservationChart />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TankerDeliveries />
            <CommunicationHub />
          </div>
        </main>
      </div>
      <Footer />
    </div>
  )
}
