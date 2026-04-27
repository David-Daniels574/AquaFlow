// Custom hooks for API calls using React Query

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  suppliersAPI,
  consumptionAPI,
  leakDetectionAPI,
  conservationAPI,
  societyAPI,
  tankerMarketplaceAPI,
  tankerOwnerAPI,
  authAPI,
  Supplier,
  ConsumptionReport,
  ConservationSummary,
  SocietyDashboard,
  ConservationTip,
  Challenge,
  UserChallenge,
  OwnerBooking,
  OwnerDashboard,
  OwnerEarnings,
} from '../services/api';

// Auth hooks
export const useLogin = () => {
  return useMutation({
    mutationFn: authAPI.login,
    onSuccess: () => {
      // Invalidate user-related queries after successful login
    },
  });
};

export const useRegister = () => {
  return useMutation({
    mutationFn: authAPI.register,
  });
};

export const useProfile = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: authAPI.getProfile,
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authAPI.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });
};

// Suppliers hooks
export const useSuppliers = () => {
  return useQuery({
    queryKey: ['suppliers'],
    queryFn: suppliersAPI.getSuppliers,
  });
};

export const useMarketplaceTankers = () => {
  return useQuery({
    queryKey: ['marketplace-tankers'],
    queryFn: tankerMarketplaceAPI.getTankers,
  });
};

export const useCreateMarketplaceBooking = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: tankerMarketplaceAPI.createBooking,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-tankers'] });
      queryClient.invalidateQueries({ queryKey: ['owner-bookings'] });
      queryClient.invalidateQueries({ queryKey: ['owner-dashboard'] });
    },
  });
};

export const useBookTanker = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: suppliersAPI.bookTanker,
    onSuccess: () => {
      // Invalidate orders or suppliers queries if needed
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
    },
  });
};

export const useTrackOrder = (orderId: number) => {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => suppliersAPI.trackOrder(orderId),
    enabled: !!orderId,
  });
};

// Consumption hooks
export const useLogReading = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: consumptionAPI.logReading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['consumption'] });
    },
  });
};

export const useConsumptionReport = (period: 'daily' | 'weekly' | 'monthly' = 'daily', detailed: boolean = false) => {
  return useQuery({
    queryKey: ['consumption', period, detailed],
    queryFn: () => consumptionAPI.getConsumptionReport(period, detailed),
  });
};

// Leak detection hooks
export const useLeakDetection = (threshold: number = 5.0) => {
  return useQuery({
    queryKey: ['leak-detection', threshold],
    queryFn: () => leakDetectionAPI.getLeakDetection(threshold),
  });
};

// Conservation hooks
export const useConservationTips = (location: string = 'urban_india') => {
  return useQuery({
    queryKey: ['conservation-tips', location],
    queryFn: () => conservationAPI.getConservationTips(location),
  });
};

export const useChallenges = () => {
  return useQuery({
    queryKey: ['challenges'],
    queryFn: conservationAPI.getChallenges,
  });
};

export const useStartChallenge = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: conservationAPI.startChallenge,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-challenges'] });
      queryClient.invalidateQueries({ queryKey: ['conservation-summary'] });
    },
  });
};

export const useUserChallenges = () => {
  return useQuery({
    queryKey: ['user-challenges'],
    queryFn: conservationAPI.getUserChallenges,
  });
};

export const useUpdateChallengeProgress = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userChallengeId, progress }: { userChallengeId: number; progress: number }) =>
      conservationAPI.updateChallengeProgress(userChallengeId, progress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-challenges'] });
      queryClient.invalidateQueries({ queryKey: ['conservation-summary'] });
    },
  });
};

export const useConservationSummary = () => {
  return useQuery({
    queryKey: ['conservation-summary'],
    queryFn: conservationAPI.getConservationSummary,
  });
};

// Society hooks
export const useSocietyDashboard = () => {
  return useQuery({
    queryKey: ['society-dashboard'],
    queryFn: societyAPI.getSocietyDashboard,
  });
};

export const usePlaceBulkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: societyAPI.placeBulkOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['society-dashboard'] });
    },
  });
};

// Tanker owner hooks
export const useOwnerDashboard = () => {
  return useQuery<OwnerDashboard>({
    queryKey: ['owner-dashboard'],
    queryFn: tankerOwnerAPI.getDashboard,
  });
};

export const useOwnerEarnings = () => {
  return useQuery<OwnerEarnings>({
    queryKey: ['owner-earnings'],
    queryFn: tankerOwnerAPI.getEarnings,
  });
};

export const useOwnerTankers = () => {
  return useQuery<Supplier[]>({
    queryKey: ['owner-tankers'],
    queryFn: tankerOwnerAPI.getTankers,
  });
};

export const useOwnerCreateTanker = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: tankerOwnerAPI.createTanker,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['owner-tankers'] });
      queryClient.invalidateQueries({ queryKey: ['owner-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-tankers'] });
    },
  });
};

export const useOwnerUpdateTanker = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tankerId, data }: { tankerId: number; data: any }) => tankerOwnerAPI.updateTanker(tankerId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['owner-tankers'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-tankers'] });
    },
  });
};

export const useOwnerDeleteTanker = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: tankerOwnerAPI.deleteTanker,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['owner-tankers'] });
      queryClient.invalidateQueries({ queryKey: ['owner-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-tankers'] });
    },
  });
};

export const useOwnerUpdateTankerStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tankerId, status }: { tankerId: number; status: 'available' | 'booked' | 'maintenance' }) =>
      tankerOwnerAPI.updateTankerStatus(tankerId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['owner-tankers'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-tankers'] });
    },
  });
};

export const useOwnerBookings = () => {
  return useQuery<OwnerBooking[]>({
    queryKey: ['owner-bookings'],
    queryFn: tankerOwnerAPI.getBookings,
  });
};

export const useOwnerUpdateBookingStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bookingId, status }: { bookingId: number; status: 'pending' | 'confirmed' | 'in_transit' | 'completed' | 'cancelled' }) =>
      tankerOwnerAPI.updateBookingStatus(bookingId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['owner-bookings'] });
      queryClient.invalidateQueries({ queryKey: ['owner-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['owner-earnings'] });
      queryClient.invalidateQueries({ queryKey: ['owner-tankers'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-tankers'] });
    },
  });
};
