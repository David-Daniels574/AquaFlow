import { Button } from "./ui/button"
import { Search, Menu } from "lucide-react"

export default function Header({ onMenuClick }) {
  return (
    <header className="bg-blue-600 text-white px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onMenuClick}
            className="p-2 rounded-md text-white hover:bg-blue-700 transition-colors"
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex items-center space-x-8">
            <div className="text-2xl font-bold">✱</div>
            <nav className="hidden lg:flex items-center space-x-6">
              <a href="#" className="hover:text-blue-200 transition-colors">
                Water Tanker Marketplace
              </a>
              <a href="#" className="hover:text-blue-200 transition-colors">
                Consumption Tracking
              </a>
              <a href="#" className="hover:text-blue-200 transition-colors">
                Leak Detection
              </a>
              <a href="#" className="hover:text-blue-200 transition-colors font-semibold">
                Conservation Hub
              </a>
              <a href="#" className="hover:text-blue-200 transition-colors">
                Society Dashboard
              </a>
            </nav>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search for water tankers by location"
              className="pl-10 pr-4 py-2 rounded-md text-gray-900 w-80"
            />
          </div>
          <Button variant="outline" className="text-blue-600 border-white hover:bg-blue-50 bg-transparent">
            Login
          </Button>
          <Button className="bg-white text-blue-600 hover:bg-gray-100">Sign Up</Button>
        </div>
      </div>
    </header>
  )
}
