import { Button } from "./ui/button"

export default function ChallengesSection() {
  const challenges = [
    {
      title: "No-Drip Day",
      description:
        "Can you go a full day without any unnecessary water drips or leaks in your household? Stay vigilant and save every drop!",
      progress: 75,
      color: "bg-blue-600",
    },
    {
      title: "Garden Smart Week",
      description:
        "Implement 3 water-saving techniques in your garden this week, such as mulching, drip irrigation, or choosing drought-tolerant plants.",
      progress: 50,
      color: "bg-blue-600",
    },
    {
      title: "Water Audit Week",
      description:
        "Track your household water usage for a full week to identify key areas for reduction and discover where you can make the biggest impact.",
      progress: 30,
      color: "bg-blue-600",
    },
  ]

  return (
    <section className="mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Engage & Transform</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {challenges.map((challenge, index) => (
          <div key={index} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">{challenge.title}</h3>
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">{challenge.description}</p>

            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{challenge.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`${challenge.color} h-2 rounded-full transition-all duration-300`}
                  style={{ width: `${challenge.progress}%` }}
                ></div>
              </div>
            </div>

            <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">View Challenge</Button>
          </div>
        ))}
      </div>
    </section>
  )
}
