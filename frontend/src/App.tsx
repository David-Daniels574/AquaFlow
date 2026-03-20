import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import CommunityPage from "@/pages/CommunityPage";
import MarketplacePage from "@/pages/MarketplacePage";
import ConsumptionPage from "@/pages/ConsumptionPage";
import ConservationHubPage from "@/pages/ConservationHubPage";
import SocietyDashboardPage from "@/pages/SocietyDashboardPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import ProfilePage from "@/pages/ProfilePage";
import OwnerDashboardPage from "@/pages/OwnerDashboardPage";
import OwnerTankersPage from "@/pages/OwnerTankersPage";
import OwnerBookingsPage from "@/pages/OwnerBookingsPage";
import OwnerEarningsPage from "@/pages/OwnerEarningsPage";
import { useEffect } from "react";
import { getAuthToken, getCurrentUserRole } from "@/services/api";

const queryClient = new QueryClient();

// Protected route component
const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) => {
  const token = getAuthToken();
  const role = getCurrentUserRole();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles?.length && (!role || !allowedRoles.includes(role))) {
    return <Navigate to="/marketplace" replace />;
  }

  return <>{children}</>;
};

const App = () => {
  // Check for token on app load and ensure it's properly set
  useEffect(() => {
    const token = getAuthToken();
    console.log("Auth token on app load:", token ? "Present" : "Not found");
    
    // Force a re-render when token changes
    const handleStorageChange = () => {
      console.log("Local storage changed, checking token");
      getAuthToken(); // This refreshes the token from localStorage
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={
              <Navigate to="/login" replace />
            } />
            <Route path="/marketplace" element={
              <Layout>
                <ProtectedRoute>
                  <MarketplacePage />
                </ProtectedRoute>
              </Layout>
            } />
            <Route path="/consumption" element={
              <Layout>
                <ProtectedRoute>
                  <ConsumptionPage />
                </ProtectedRoute>
              </Layout>
            } />
            <Route path="/conservation" element={
              <Layout>
                <ProtectedRoute>
                  <ConservationHubPage />
                </ProtectedRoute>
              </Layout>
            } />
            <Route
              path="/society"
              element={
                <Layout>
                  <ProtectedRoute>
                    <SocietyDashboardPage />
                  </ProtectedRoute>
                </Layout>
              }
            />
            <Route
              path="/profile"
              element={
                <Layout>
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                </Layout>
              }
            />
            <Route
              path="/owner-dashboard"
              element={
                <Layout>
                  <ProtectedRoute allowedRoles={["tanker_owner", "supplier"]}>
                    <OwnerDashboardPage />
                  </ProtectedRoute>
                </Layout>
              }
            />
            <Route
              path="/owner-dashboard/tankers"
              element={
                <Layout>
                  <ProtectedRoute allowedRoles={["tanker_owner", "supplier"]}>
                    <OwnerTankersPage />
                  </ProtectedRoute>
                </Layout>
              }
            />
            <Route
              path="/owner-dashboard/bookings"
              element={
                <Layout>
                  <ProtectedRoute allowedRoles={["tanker_owner", "supplier"]}>
                    <OwnerBookingsPage />
                  </ProtectedRoute>
                </Layout>
              }
            />
            <Route
              path="/owner-dashboard/earnings"
              element={
                <Layout>
                  <ProtectedRoute allowedRoles={["tanker_owner", "supplier"]}>
                    <OwnerEarningsPage />
                  </ProtectedRoute>
                </Layout>
              }
            />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
