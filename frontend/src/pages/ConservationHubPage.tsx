import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  useChallenges,
  useConservationSummary,
  useConservationTips,
  useStartChallenge,
  useUpdateChallengeProgress,
  useUserChallenges,
} from "@/hooks/useAPI";
import { useToast } from "@/hooks/use-toast";

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-white rounded-lg shadow p-6 flex flex-col items-center justify-center">
      <h3 className="text-gray-500 text-sm">{title}</h3>
      <p className="text-2xl font-bold text-blue-600 mt-2">{value}</p>
    </div>
  );
}

export default function ConservationHubPage() {
  const { toast } = useToast();

  const {
    data: summary,
    isLoading: isSummaryLoading,
    error: summaryError,
  } = useConservationSummary();
  const {
    data: tips,
    isLoading: isTipsLoading,
    error: tipsError,
  } = useConservationTips("urban_india");
  const {
    data: challenges,
    isLoading: isChallengesLoading,
    error: challengesError,
  } = useChallenges();
  const { data: userChallenges, isLoading: isUserChallengesLoading } = useUserChallenges();

  const { mutate: startChallenge, isPending: isStartingChallenge } = useStartChallenge();
  const { mutate: updateProgress, isPending: isUpdatingProgress } = useUpdateChallengeProgress();

  const userChallengeByChallengeId = useMemo(() => {
    const map = new Map<number, (typeof userChallenges)[number]>();
    (userChallenges || []).forEach((uc) => {
      map.set(uc.challenge_id, uc);
    });
    return map;
  }, [userChallenges]);

  const suggestedChallenge = useMemo(() => {
    if (!challenges?.length) return undefined;
    return challenges.find((c) => {
      const uc = userChallengeByChallengeId.get(c.id);
      return !uc || uc.status !== "completed";
    });
  }, [challenges, userChallengeByChallengeId]);

  const handleQuickJoin = () => {
    if (!suggestedChallenge) {
      toast({
        title: "No challenge available",
        description: "You have already completed all listed challenges.",
      });
      return;
    }

    const existing = userChallengeByChallengeId.get(suggestedChallenge.id);
    if (existing) {
      toast({
        title: "Challenge already active",
        description: `Continue your progress in ${suggestedChallenge.name}.`,
      });
      return;
    }

    startChallenge(suggestedChallenge.id, {
      onSuccess: () => {
        toast({ title: "Challenge joined", description: suggestedChallenge.name });
      },
      onError: (error: Error) => {
        toast({
          variant: "destructive",
          title: "Could not join challenge",
          description: error.message,
        });
      },
    });
  };

  const handleProgressUpdate = (userChallengeId: number, currentProgress: number) => {
    const nextProgress = Math.min(100, currentProgress + 20);
    updateProgress(
      { userChallengeId, progress: nextProgress },
      {
        onSuccess: () => {
          toast({
            title: nextProgress >= 100 ? "Challenge completed" : "Progress updated",
            description: `Current progress: ${nextProgress}%`,
          });
        },
        onError: (error: Error) => {
          toast({
            variant: "destructive",
            title: "Could not update progress",
            description: error.message,
          });
        },
      }
    );
  };

  const hasAnyError = summaryError || tipsError || challengesError;

  return (
    <motion.main
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex-1 p-6 space-y-8"
    >
      <section className="bg-gradient-to-r from-blue-100 to-blue-50 rounded-lg shadow-lg p-8 flex flex-col md:flex-row items-center justify-between relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/savewater.jpg')] bg-cover bg-center opacity-10"></div>
        <div className="md:w-1/2 text-center md:text-left relative z-10">
          <h1 className="text-3xl font-bold text-gray-800 mb-4">Your Journey to Water Wisdom</h1>
          <p className="text-gray-600 text-lg mb-6">
            Discover practical tips, join measurable challenges, and track your progress with live backend data.
          </p>
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span>{isTipsLoading ? "Loading tips..." : `${tips?.length || 0} tips available`}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span>{isChallengesLoading ? "Loading challenges..." : `${challenges?.length || 0} challenges`}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span>{isUserChallengesLoading ? "Syncing progress..." : `${userChallenges?.length || 0} started`}</span>
            </div>
          </div>
          <button
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-lg disabled:opacity-60"
            onClick={handleQuickJoin}
            disabled={isStartingChallenge || isChallengesLoading || !challenges?.length}
          >
            {isStartingChallenge ? "Joining..." : "Join a Challenge"}
          </button>
        </div>
        <div className="mt-6 md:mt-0 md:ml-8 w-full md:w-1/3 relative">
          <img src="/savewater.jpg" alt="Hands holding water" className="w-full rounded-lg shadow-lg" />
          <div className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center">
            <span className="text-lg">💧</span>
          </div>
          <div className="absolute -bottom-2 -left-2 w-6 h-6 bg-green-400 rounded-full flex items-center justify-center">
            <span className="text-sm">🌱</span>
          </div>
        </div>
      </section>

      {hasAnyError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 text-sm">
          Some conservation data could not be loaded. Please check backend connectivity and authentication.
        </div>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-4">Your Conservation Progress</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <StatCard
            title="Water Saved This Month"
            value={isSummaryLoading ? "..." : `${Math.round(summary?.water_saved_this_month || 0)} Liters`}
          />
          <StatCard title="Active Challenges" value={isSummaryLoading ? "..." : summary?.active_challenges || 0} />
          <StatCard title="Eco-Points Earned" value={isSummaryLoading ? "..." : summary?.eco_points_earned || 0} />
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Learn & Implement</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h3 className="font-bold mb-2">Water-Saving Tips (from backend)</h3>
            {isTipsLoading ? (
              <p className="text-sm text-gray-500">Loading tips...</p>
            ) : !tips?.length ? (
              <p className="text-sm text-gray-500">No tips available for this location.</p>
            ) : (
              <ul className="space-y-2">
                {tips.slice(0, 6).map((tip, idx) => (
                  <li key={`${tip.title}-${idx}`} className="p-3 bg-gray-50 rounded border">
                    💧 <strong>{tip.title}:</strong> {tip.content}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <h4 className="font-semibold">Suggested Challenge</h4>
              <p className="text-gray-600 text-sm mt-1">
                {suggestedChallenge
                  ? `${suggestedChallenge.name} — save up to ${suggestedChallenge.water_save_potential} L and earn ${suggestedChallenge.eco_points} points.`
                  : "You have completed all current challenges. Great work!"}
              </p>
              <button
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-60"
                onClick={handleQuickJoin}
                disabled={isStartingChallenge || !suggestedChallenge}
              >
                {isStartingChallenge ? "Starting..." : "Start Suggested Challenge"}
              </button>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <h4 className="font-semibold">Live Progress Sync</h4>
              <p className="text-gray-600 text-sm mt-1">
                Your challenge status, eco-points, and monthly water savings are synced with the backend in real-time.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Engage & Transform</h2>

        {isChallengesLoading || isUserChallengesLoading ? (
          <div className="text-sm text-gray-500">Loading challenges...</div>
        ) : !challenges?.length ? (
          <div className="text-sm text-gray-500">No challenges available right now.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {challenges.map((challenge) => {
              const userChallenge = userChallengeByChallengeId.get(challenge.id);
              const progress = Math.round(userChallenge?.progress || 0);
              const isCompleted = userChallenge?.status === "completed";

              return (
                <div key={challenge.id} className="bg-white rounded-lg shadow p-4">
                  <h4 className="font-semibold">{challenge.name}</h4>
                  <p className="text-gray-600 text-sm mt-1">{challenge.short_desc}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    Save potential: {challenge.water_save_potential} L • Reward: {challenge.eco_points} points
                  </p>

                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${progress}%` }}></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Progress: {progress}%</p>

                  {!userChallenge ? (
                    <button
                      className="mt-3 px-4 py-2 bg-blue-600 text-white rounded text-sm w-full disabled:opacity-60"
                      onClick={() => startChallenge(challenge.id)}
                      disabled={isStartingChallenge}
                    >
                      Start Challenge
                    </button>
                  ) : (
                    <button
                      className="mt-3 px-4 py-2 bg-blue-600 text-white rounded text-sm w-full disabled:opacity-60"
                      onClick={() => handleProgressUpdate(userChallenge.id, progress)}
                      disabled={isCompleted || isUpdatingProgress}
                    >
                      {isCompleted ? "Completed" : "Add 20% Progress"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </motion.main>
  );
}
