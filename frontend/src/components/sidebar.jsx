import { Home, BarChart3, AlertTriangle, Leaf, Users } from "lucide-react"

export default function Sidebar({ isOpen, onClose, currentPage, onPageChange }) {
  const menuItems = [
    { icon: Home, label: "Water Tanker Marketplace", page: "Water Tanker Marketplace" },
    { icon: BarChart3, label: "Consumption Tracking", page: "Consumption Tracking" },
    { icon: AlertTriangle, label: "Leak Detection", page: "Leak Detection" },
    { icon: Leaf, label: "Conservation Hub", page: "Conservation Hub" },
    { icon: Users, label: "Society Dashboard", page: "Society Dashboard" },
  ]

  const handlePageChange = (page) => {
    onPageChange(page)
    onClose()
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200 
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        
        <nav className="p-4">
          <ul className="space-y-2">
            {menuItems.map((item, index) => {
              const Icon = item.icon
              const isActive = currentPage === item.page
              return (
                <li key={index}>
                  <button
                    onClick={() => handlePageChange(item.page)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md transition-colors text-left ${
                      isActive
                        ? "bg-blue-50 text-blue-600 border-r-2 border-blue-600"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-sm">{item.label}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>
    </>
  )
}
