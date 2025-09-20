import { Home, BarChart3, AlertTriangle, Leaf, Users } from "lucide-react"

export default function Sidebar({ isOpen, onClose }) {
  const menuItems = [
    { icon: Home, label: "Water Tanker Marketplace", active: false },
    { icon: BarChart3, label: "Consumption Tracking", active: false },
    { icon: AlertTriangle, label: "Leak Detection", active: false },
    { icon: Leaf, label: "Conservation Hub", active: true },
    { icon: Users, label: "Society Dashboard", active: false },
  ]

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
              return (
                <li key={index}>
                  <a
                    href="#"
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md transition-colors ${
                      item.active
                        ? "bg-blue-50 text-blue-600 border-r-2 border-blue-600"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                    onClick={onClose}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-sm">{item.label}</span>
                  </a>
                </li>
              )
            })}
          </ul>
        </nav>
      </aside>
    </>
  )
}
