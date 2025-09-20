import { Facebook, Twitter, Linkedin, Instagram } from "lucide-react"

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Quick Links</span>
            <span className="text-sm text-gray-600">Legal</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
            <Facebook className="w-5 h-5" />
          </a>
          <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
            <Twitter className="w-5 h-5" />
          </a>
          <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
            <Linkedin className="w-5 h-5" />
          </a>
          <a href="#" className="text-gray-400 hover:text-gray-600 transition-colors">
            <Instagram className="w-5 h-5" />
          </a>
        </div>
      </div>
    </footer>
  )
}
