// src/pages/conservationhub.jsx

import { useState } from "react"
import Header from "../components/header"
import Sidebar from "../components/sidebar"
import HeroSection from "../components/hero-section"
import ProgressSection from "../components/progress-section"
import LearnSection from "../components/learn-section"
import ChallengesSection from "../components/challenges-section"
import Footer from "../components/footer"

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      <div className="flex">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 p-6">
          <HeroSection />
          <ProgressSection />
          <LearnSection />
          <ChallengesSection />
        </main>
      </div>
      <Footer />
    </div>
  )
}