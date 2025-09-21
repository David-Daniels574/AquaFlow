// Custom hooks for API calls using React Query

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  suppliersAPI,
  consumptionAPI,
  leakDetectionAPI,
  conservationAPI,
  societyAPI,
  authAPI,
  Supplier,
  ConsumptionReport,
  ConservationSummary,
  SocietyDashboard,
  ConservationTip,
  Challenge,
  UserChallenge,
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
