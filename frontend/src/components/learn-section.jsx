import { Button } from "./ui/button"
import { Wrench, Clock, Droplet, Zap } from "lucide-react"

export default function LearnSection() {
  const tips = [
    {
      icon: Wrench,
      title: "Fix Leaky Faucets",
      description: "A small drip can waste thousands of liters per month. Check and fix all leaks promptly.",
    },
    {
      icon: Clock,
      title: "Shorten Showers",
      description: "Reduce your shower time by a few minutes to save significant amounts of water daily.",
    },
    {
      icon: Droplet,
      title: "Harvest Rainwater",
      description: "Install a simple system to collect rainwater for gardening and non-potable uses.",
    },
    {
      icon: Zap,
      title: "Efficient Appliances",
      description: "Upgrade to water-efficient washing machines and dishwashers for long-term savings.",
    },
  ]

  const articles = [
    {
      title: "Monsoon Harvest: Rainwater Harvesting Basics",
      description:
        "Learn how to effectively collect and utilize rainwater during the monsoon season to supplement your household needs and reduce dependency on municipal water.",
      image: "/rainwater-harvesting.svg",
      category: "Water Collection",
    },
    {
      title: "Smart Gardening: Water-Wise Landscaping",
      description:
        "Explore drought-resistant plants and efficient irrigation techniques for a beautiful, water-saving garden that thrives with minimal water usage.",
      image: "/smart-gardening.svg",
      category: "Gardening",
    },
  ]

  return (
    <section className="mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Learn & Implement</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Water-Saving Tips</h3>
          <div className="space-y-4">
            {tips.map((tip, index) => {
              const Icon = tip.icon
              return (
                <div key={index} className="flex items-start space-x-3 p-4 bg-white rounded-lg border border-gray-200">
                  <div className="flex-shrink-0">
                    <Icon className="w-6 h-6 text-green-600 mt-1" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 mb-1">{tip.title}</h4>
                    <p className="text-sm text-gray-600">{tip.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="space-y-6">
          {articles.map((article, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <img src={article.image || "/placeholder.svg"} alt={article.title} className="w-full h-48 object-cover" />
              <div className="p-6">
                <h4 className="font-semibold text-gray-900 mb-2">{article.title}</h4>
                <p className="text-sm text-gray-600 mb-4 leading-relaxed">{article.description}</p>
                <Button variant="outline" size="sm">
                  Read More
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
