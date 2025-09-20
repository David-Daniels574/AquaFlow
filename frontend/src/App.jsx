import { useState } from 'react'
import './App.css'
import './index.css'
import ConservationHub from './pages/ConservationHub.jsx'
import SocietyDashboard from './pages/SocietyDashboard.jsx'

function App() {
  const [currentPage, setCurrentPage] = useState('Conservation Hub')

  const renderPage = () => {
    switch (currentPage) {
      case 'Conservation Hub':
        return <ConservationHub currentPage={currentPage} onPageChange={setCurrentPage} />
      case 'Society Dashboard':
        return <SocietyDashboard currentPage={currentPage} onPageChange={setCurrentPage} />
      default:
        return <ConservationHub currentPage={currentPage} onPageChange={setCurrentPage} />
    }
  }

  return (
    <>
      {renderPage()}
    </>
  )
}

export default App
