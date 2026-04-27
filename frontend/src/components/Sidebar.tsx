import { NavLink } from "react-router-dom";
import { 
  Truck, 
  BarChart3, 
  AlertTriangle, 
  Leaf, 
  Building2,
  Home,
  Package,
  ClipboardList,
  Wallet,
} from "lucide-react";
import { motion } from "framer-motion";
import { getCurrentUserRole } from "@/services/api";

export function Sidebar() {
  const role = getCurrentUserRole();

  const navItems = [
    { 
      name: "Water Tanker Marketplace", 
      path: "/marketplace", 
      icon: Truck 
    },
    { 
      name: "Consumption Tracking", 
      path: "/consumption", 
      icon: BarChart3 
    },
    { 
      name: "Conservation Hub", 
      path: "/conservation", 
      icon: Leaf 
    },
    { 
      name: "Society Dashboard", 
      path: "/society", 
      icon: Building2 
    },
    ...(role === "tanker_owner" || role === "supplier" ? [
      { name: "Owner Dashboard", path: "/owner-dashboard", icon: Home, end: true },
      { name: "My Tankers", path: "/owner-dashboard/tankers", icon: Package },
      { name: "Bookings", path: "/owner-dashboard/bookings", icon: ClipboardList },
      { name: "Earnings", path: "/owner-dashboard/earnings", icon: Wallet },
    ] : []),
  ];

  return (
    <aside className="w-64 bg-sidebar-bg border-r border-border h-[calc(100vh-80px)] p-4 relative">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-30"></div>
      
      <nav className="space-y-2 relative z-10">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={!!item.end}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-sidebar-active text-white"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                }`
              }
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Icon className="h-4 w-4" />
              </motion.div>
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}