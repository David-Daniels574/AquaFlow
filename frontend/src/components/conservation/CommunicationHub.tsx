import React from "react";
import { useBroadcasts } from "@/hooks/useCommunity";
import { Bell, ArrowRight, Megaphone } from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

export function CommunicationHub() {
  const { data: broadcasts, isLoading } = useBroadcasts();
  const navigate = useNavigate();

  if (isLoading) return (
    <div className="h-full min-h-[300px] bg-slate-100/50 animate-pulse rounded-2xl border border-slate-200" />
  );

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 flex flex-col h-full min-h-[300px] relative overflow-hidden group">
      
      {/* Decorative Background Blur */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-blue-500/5 rounded-full blur-3xl -mr-16 -mt-16 transition-all group-hover:bg-blue-500/10 pointer-events-none" />

      {/* Header Section */}
      <div className="flex items-center justify-between mb-6 z-10">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 rounded-xl text-blue-600 shadow-sm shadow-blue-100">
            <Megaphone className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-lg leading-tight">Community Board</h3>
            <p className="text-xs text-slate-400">Latest announcements</p>
          </div>
        </div>
        
        {/* Pulsing Dot if there are messages */}
        {broadcasts?.length > 0 && (
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500 shadow-sm"></span>
          </span>
        )}
      </div>

      {/* Broadcast List Area */}
      <div className="flex-1 space-y-3 overflow-y-auto pr-2 custom-scrollbar z-10">
        {broadcasts?.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 py-8">
            <Bell className="w-10 h-10 mb-3 opacity-10" />
            <p className="text-sm font-medium">No new announcements</p>
            <p className="text-xs opacity-60">Enjoy your day!</p>
          </div>
        ) : (
          broadcasts?.map((item: any, idx: number) => (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              key={item.id}
              className="p-4 bg-slate-50/80 hover:bg-white rounded-xl border border-slate-100 hover:border-blue-200 hover:shadow-md transition-all duration-300 group/item cursor-default"
            >
              <h4 className="font-semibold text-slate-800 text-sm mb-1 group-hover/item:text-blue-700 transition-colors">
                {item.title}
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                {item.content}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                  {new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                </p>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Footer / CTA */}
      <motion.button
        whileHover={{ x: 5 }}
        onClick={() => navigate("/community")}
        className="mt-6 flex items-center justify-between text-sm font-bold text-blue-600 hover:text-blue-700 w-full group z-10 pt-4 border-t border-slate-50"
      >
        <span>Join Discussions</span>
        <div className="p-1.5 bg-blue-50 rounded-full group-hover:bg-blue-100 transition-colors">
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
        </div>
      </motion.button>
    </div>
  );
}