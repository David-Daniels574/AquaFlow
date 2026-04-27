import { LogReadingForm } from "@/components/consumption/LogReadingForm";
import { ConsumptionCharts } from "@/components/consumption/ConsumptionCharts";
import { RecentReadings } from "@/components/consumption/RecentReadings";
import { motion } from "framer-motion";

export default function ConsumptionPage() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-8 overflow-hidden">
        <div className="absolute inset-0 bg-[url('/savewater.jpg')] bg-cover bg-center opacity-10"></div>
        <div className="relative z-10 space-y-4">
          <h1 className="text-4xl font-bold text-foreground">Manual Consumption Tracking</h1>
          <p className="text-muted-foreground text-lg max-w-2xl">
            Track your water consumption manually and monitor usage patterns to optimize your water usage.
          </p>
          <div className="flex items-center space-x-6 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-status-success rounded-full"></div>
              <span>Real-time tracking</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-primary rounded-full"></div>
              <span>Usage analytics</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-status-warning rounded-full"></div>
              <span>Conservation tips</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid lg:grid-cols-4 gap-6">
        <motion.div 
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <LogReadingForm />
        </motion.div>
        
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-3"
        >
          <ConsumptionCharts />
        </motion.div>
      </div>
      
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <RecentReadings />
      </motion.div>
    </motion.div>
  );
}