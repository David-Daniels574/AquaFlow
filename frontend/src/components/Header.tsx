import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Droplet, User } from "lucide-react";
import { motion } from "framer-motion";
import { getAuthToken, clearAuthToken, getCurrentUserRole } from "@/services/api";
import { useState, useEffect } from "react";

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const token = getAuthToken();
    setIsAuthenticated(!!token);
    setRole(getCurrentUserRole());
  }, [location, getAuthToken]);

  const handleLogout = () => {
    clearAuthToken();
    setIsAuthenticated(false);
    setRole(null);
    navigate("/login");
  };

  const isOwner = role === "tanker_owner" || role === "supplier";

  const navItems = [
    { 
      name: "Water Tanker Marketplace", 
      path: "/marketplace"
    },
    ...(!isOwner ? [
      { 
        name: "Consumption Tracking", 
        path: "/consumption"
      },
      { 
        name: "Conservation Hub", 
        path: "/conservation"
      },
      { 
        name: "Society Dashboard", 
        path: "/society" 
      },
    ] : []),
    ...(isOwner ? [
      { name: "Owner Dashboard", path: "/owner-dashboard",  end: true },
      { name: "My Tankers", path: "/owner-dashboard/tankers" },
      { name: "Bookings", path: "/owner-dashboard/bookings" },
      { name: "Earnings", path: "/owner-dashboard/earnings" },
    ] : []),
  ];
  
  return (
    <header className="bg-primary text-primary-foreground px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <Droplet className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AquaFlow</h1>
              <p className="text-xs text-white/80">Water Management</p>
            </div>
          </div>
          
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-4 py-2 text-sm font-medium rounded-lg transition-colors relative ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "hover:bg-white/10 text-white/80"
                  }`
                }
              >
                {item.name}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search for water tankers by location"
              className="pl-10 w-80 bg-white/10 border-white/20 text-white placeholder:text-white/60"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            {isAuthenticated ? (
              <>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-white/20 text-zinc-950 hover:bg-white/10"
                  onClick={() => navigate("/profile")}
                >
                  <User className="h-4 w-4 mr-2" />
                  Profile
                </Button>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="bg-white text-primary hover:bg-white/90"
                  onClick={handleLogout}
                >
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-white/20 text-white hover:bg-white/10"
                  onClick={() => navigate("/login")}
                >
                  Login
                </Button>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="bg-white text-primary hover:bg-white/90"
                  onClick={() => navigate("/register")}
                >
                  Sign Up
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}