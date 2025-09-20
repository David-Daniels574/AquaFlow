import { Button } from "./ui/button"

export default function HeroSection() {
  return (
    <section className="bg-gradient-to-r from-gray-100 to-gray-200 rounded-lg p-8 mb-8">
      <div className="flex items-center justify-between">
        <div className="flex-1 pr-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4 text-balance">Your Journey to Water Wisdom</h1>
          <p className="text-gray-600 text-lg mb-6 leading-relaxed">
            Discover practical tips, engage in fun challenges, and track your progress towards a more sustainable water
            footprint. Every drop counts!
          </p>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3">Join a Challenge</Button>
        </div>
        <div className="flex-shrink-0">
          <img
            src="/placeholder.svg?height=300&width=400"
            alt="Cupped hands holding water"
            className="rounded-lg shadow-lg"
          />
        </div>
      </div>
    </section>
  )
}
