// API service layer for communicating with Flask backend

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

// Types for API responses
export interface Supplier {
  id: number;
  name: string;
  contact: string;
  photo_url?: string;
  area: string;
  city: string;
  rating: number;
  num_reviews: number;
  lat?: number;
  long?: number;
  offers: Array<{ quantity: number; cost: number }>;
  starting_from?: number;
  estimated_eta?: number;
  vehicle_number?: string;
  capacity?: number;
  type?: string;
  status?: "available" | "booked" | "maintenance";
  is_available?: boolean;
  price_per_liter?: number;
  base_delivery_fee?: number;
  service_areas?: string[];
  amenities?: string[];
  description?: string;
  owner_id?: number;
}

export interface OwnerDashboard {
  total_tankers: number;
  active_bookings: number;
  this_month_earnings: number;
  average_rating: number;
  pending_bookings: number;
  recent_activity: Array<{
    booking_id: number;
    tanker_id: number;
    status: string;
    total_amount: number;
    quantity: number;
    created_at: string;
  }>;
}

export interface OwnerBooking {
  id: number;
  tanker_id: number;
  tanker_vehicle_number: string;
  customer: {
    id: number;
    username: string;
    email: string;
  };
  delivery_address: string;
  delivery_pincode?: string;
  quantity: number;
  total_amount: number;
  status: "pending" | "confirmed" | "in_transit" | "completed" | "cancelled";
  scheduled_time?: string;
  delivered_time?: string;
  created_at: string;
}

export interface OwnerEarnings {
  total_earnings: number;
  completed_orders: number;
  monthly: Array<{ month: string; amount: number }>;
  by_tanker: Array<{ tanker_id: number; vehicle_number: string; amount: number }>;
}

export interface LeakEvent {
  date: string;
  loss: number;
  severity: string;
  description: string;
}

export interface WaterReading {
  timestamp: string;
  reading: number;
}

export interface DailyBreakdown {
  date: string;
  usage: number;
}

export interface ConsumptionReport {
  period: string;
  total_usage_liters: number;
  daily_breakdown: DailyBreakdown[];
}

export interface ConservationSummary {
  water_saved_this_month: number;
  active_challenges: number;
  eco_points_earned: number;
}

export interface SocietyDashboard {
  monthly_consumption: Record<number, number>;
  tankers_ordered_ytd: number;
  total_volume_ytd: number;
  active_initiatives: number;
  water_saved: number;
  conservation_impact: {
    active: number;
    pending: number;
    completed: number;
  };
  scheduled_deliveries: Array<{
    supplier: string;
    date: string;
    time: string;
    volume: number;
    status: string;
  }>;
}

export interface ConservationTip {
  title: string;
  content: string;
}

export interface Challenge {
  id: number;
  name: string;
  short_desc: string;
  full_desc: string;
  water_save_potential: number;
  eco_points: number;
}

export interface UserChallenge {
  id: number;
  challenge_id: number;
  name: string;
  short_desc: string;
  full_desc: string;
  progress: number;
  status: string;
  start_date?: string;
  end_date?: string;
  water_saved: number;
  eco_points_earned: number;
}

// Auth token management
let authToken: string | null = null;

export const setAuthToken = (token: string) => {
  authToken = token;
  localStorage.setItem('authToken', token);
};

export const getAuthToken = (): string | null => {
  if (!authToken) {
    authToken = localStorage.getItem('authToken');
  }
  return authToken;
};

export const getAuthClaims = (): { role?: string; sub?: string } | null => {
  const token = getAuthToken();
  if (!token) return null;

  try {
    const payload = token.split('.')[1];
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
    const decoded = JSON.parse(atob(padded));
    return decoded;
  } catch {
    return null;
  }
};

export const getCurrentUserRole = (): string | null => {
  const claims = getAuthClaims();
  const role = claims?.role;
  if (!role) return null;

  if (role === 'customer') return 'user';
  if (role === 'admin') return 'society_admin';
  return role;
};

export const clearAuthToken = () => {
  authToken = null;
  localStorage.removeItem('authToken');
};

// API Base URL is already defined at the top of the file

// Generic API request function
export const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const token = getAuthToken();
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  console.log(`Making API request to ${endpoint} with token:`, token ? 'Present' : 'Not found');

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      console.error(`API error for ${endpoint}:`, response.status, response.statusText);
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
};

// Auth API calls
export const authAPI = {
  register: async (userData: {
    username: string;
    email: string;
    password: string;
    role: string;
    society_id?: number;
    area?: string;
    city?: string;
    lat?: number;
    long?: number;
  }) => {
    return apiRequest<{ message: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  login: async (credentials: { identifier: string; password: string }) => {
    const response = await apiRequest<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    setAuthToken(response.access_token);
    return response;
  },

  getProfile: async () => {
    return apiRequest<{
      username: string;
      email: string;
      role: string;
      society_id?: number;
      area?: string;
      city?: string;
      lat?: number;
      long?: number;
    }>('/auth/profile');
  },

  updateProfile: async (profileData: {
    area?: string;
    city?: string;
    lat?: number;
    long?: number;
  }) => {
    return apiRequest<{ message: string }>('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },
};

// Suppliers API calls
export const suppliersAPI = {
  getSuppliers: async (): Promise<Supplier[]> => {
    return apiRequest<Supplier[]>('/supplier/suppliers');
  },

  bookTanker: async (orderData: {
    supplier_id: number;
    volume: number;
    price: number;
    society_id?: number;
  }) => {
    return apiRequest<{ message: string; order_id: number }>('/bookings/book_tanker', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  },

  trackOrder: async (orderId: number) => {
    return apiRequest<{
      status: string;
      lat?: number;
      long?: number;
      delivery_time?: string;
    }>(`/bookings/track_order/${orderId}`);
  },
};

// Water consumption API calls
export const consumptionAPI = {
  logReading: async (readingData: {
    reading: number;
    society_id?: number;
    timestamp?: string;
  }) => {
    return apiRequest<{ message: string }>('/analytics/log_reading', {
      method: 'POST',
      body: JSON.stringify(readingData),
    });
  },

  getConsumptionReport: async (period: 'daily' | 'weekly' | 'monthly' = 'daily', detailed: boolean = false): Promise<ConsumptionReport> => {
    const params = new URLSearchParams({
      period,
      detailed: detailed.toString(),
    });
    return apiRequest<ConsumptionReport>(`/analytics/consumption_report?${params}`);
  },
};

// Leak detection API calls
export const leakDetectionAPI = {
  getLeakDetection: async (threshold: number = 5.0) => {
    return apiRequest<{
      has_leak: boolean;
      estimated_loss: number;
      severity?: string;
      message: string;
      description?: string;
      history: LeakEvent[];
    }>(`/analytics/leak_detection?threshold=${threshold}`);
  },
};

// Conservation API calls
export const conservationAPI = {
  getConservationTips: async (location: string = 'urban_india'): Promise<ConservationTip[]> => {
    return apiRequest<ConservationTip[]>(`/gamification/conservation_tips?location=${location}`);
  },

  getChallenges: async (): Promise<Challenge[]> => {
    return apiRequest<Challenge[]>('/gamification/challenges');
  },

  startChallenge: async (challengeId: number) => {
    return apiRequest<{ message: string; user_challenge_id: number }>(`/gamification/start_challenge/${challengeId}`, {
      method: 'POST',
    });
  },

  getUserChallenges: async (): Promise<UserChallenge[]> => {
    return apiRequest<UserChallenge[]>('/gamification/user_challenges');
  },

  updateChallengeProgress: async (userChallengeId: number, progress: number) => {
    return apiRequest<{ message: string }>(`/gamification/update_challenge_progress/${userChallengeId}`, {
      method: 'PUT',
      body: JSON.stringify({ progress }),
    });
  },

  getConservationSummary: async (): Promise<ConservationSummary> => {
    return apiRequest<ConservationSummary>('/analytics/conservation_summary');
  },
};

// Society management API calls
export const societyAPI = {
  getSocietyDashboard: async (): Promise<SocietyDashboard> => {
    return apiRequest<SocietyDashboard>('/analytics/society_dashboard');
  },

  placeBulkOrder: async (orderData: {
    supplier_id: number;
    volume: number;
    price: number;
    society_id: number;
  }) => {
    return apiRequest<{ message: string; order_id: number }>('/bookings/society_bulk_order', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  },
};

export const tankerMarketplaceAPI = {
  getTankers: async (): Promise<Supplier[]> => {
    return apiRequest<Supplier[]>('/supplier/tankers');
  },

  createBooking: async (bookingData: {
    tanker_id: number;
    quantity: number;
    total_amount: number;
    delivery_address?: string;
    delivery_pincode?: string;
    scheduled_time?: string;
  }) => {
    return apiRequest<{ message: string; booking_id: number }>('/bookings/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData),
    });
  },
};

export const tankerOwnerAPI = {
  getDashboard: async (): Promise<OwnerDashboard> => {
    return apiRequest<OwnerDashboard>('/supplier/owner/dashboard');
  },

  getEarnings: async (): Promise<OwnerEarnings> => {
    return apiRequest<OwnerEarnings>('/supplier/owner/earnings');
  },

  getTankers: async (): Promise<Supplier[]> => {
    return apiRequest<Supplier[]>('/supplier/tankers/owner');
  },

  createTanker: async (tankerData: {
    vehicle_number: string;
    capacity: number;
    type: string;
    price_per_liter: number;
    base_delivery_fee: number;
    service_areas: string[];
    images: string[];
    amenities: string[];
    description?: string;
    emergency_contact?: string;
    area?: string;
    city?: string;
  }) => {
    return apiRequest<{ message: string; tanker: Supplier }>('/supplier/tankers', {
      method: 'POST',
      body: JSON.stringify(tankerData),
    });
  },

  updateTanker: async (
    tankerId: number,
    tankerData: Partial<{
      vehicle_number: string;
      capacity: number;
      type: string;
      price_per_liter: number;
      base_delivery_fee: number;
      service_areas: string[];
      images: string[];
      amenities: string[];
      description?: string;
      emergency_contact?: string;
      area?: string;
      city?: string;
      status: "available" | "booked" | "maintenance";
    }>
  ) => {
    return apiRequest<{ message: string; tanker: Supplier }>(`/supplier/tankers/${tankerId}`, {
      method: 'PUT',
      body: JSON.stringify(tankerData),
    });
  },

  deleteTanker: async (tankerId: number) => {
    return apiRequest<{ message: string }>(`/supplier/tankers/${tankerId}`, {
      method: 'DELETE',
    });
  },

  updateTankerStatus: async (tankerId: number, status: "available" | "booked" | "maintenance") => {
    return apiRequest<{ message: string; tanker: Supplier }>(`/supplier/tankers/${tankerId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  getBookings: async (): Promise<OwnerBooking[]> => {
    return apiRequest<OwnerBooking[]>('/bookings/bookings/owner');
  },

  updateBookingStatus: async (
    bookingId: number,
    status: "pending" | "confirmed" | "in_transit" | "completed" | "cancelled"
  ) => {
    return apiRequest<{ message: string }>(`/bookings/bookings/${bookingId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },
};
