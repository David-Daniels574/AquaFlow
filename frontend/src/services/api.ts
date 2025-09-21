// API service layer for communicating with Flask backend

const API_BASE_URL = 'http://localhost:5001/api';

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

export interface ConsumptionReport {
  total_consumption: number;
  average_daily: number;
  trend: string;
  readings?: WaterReading[];
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

export const clearAuthToken = () => {
  authToken = null;
  localStorage.removeItem('authToken');
};

// API Base URL is already defined at the top of the file

// Generic API request function
const apiRequest = async <T>(
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
    return apiRequest<{ message: string }>('/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  login: async (credentials: { identifier: string; password: string }) => {
    const response = await apiRequest<{ access_token: string }>('/login', {
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
    }>('/profile');
  },

  updateProfile: async (profileData: {
    area?: string;
    city?: string;
    lat?: number;
    long?: number;
  }) => {
    return apiRequest<{ message: string }>('/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },
};

// Suppliers API calls
export const suppliersAPI = {
  getSuppliers: async (): Promise<Supplier[]> => {
    return apiRequest<Supplier[]>('/suppliers');
  },

  bookTanker: async (orderData: {
    supplier_id: number;
    volume: number;
    price: number;
    society_id?: number;
  }) => {
    return apiRequest<{ message: string; order_id: number }>('/book_tanker', {
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
    }>(`/track_order/${orderId}`);
  },
};

// Water consumption API calls
export const consumptionAPI = {
  logReading: async (readingData: {
    reading: number;
    society_id?: number;
    timestamp?: string;
  }) => {
    return apiRequest<{ message: string }>('/log_reading', {
      method: 'POST',
      body: JSON.stringify(readingData),
    });
  },

  getConsumptionReport: async (period: 'daily' | 'weekly' | 'monthly' = 'daily', detailed: boolean = false): Promise<ConsumptionReport> => {
    const params = new URLSearchParams({
      period,
      detailed: detailed.toString(),
    });
    return apiRequest<ConsumptionReport>(`/consumption_report?${params}`);
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
    }>(`/leak_detection?threshold=${threshold}`);
  },
};

// Conservation API calls
export const conservationAPI = {
  getConservationTips: async (location: string = 'urban_india'): Promise<ConservationTip[]> => {
    return apiRequest<ConservationTip[]>(`/conservation_tips?location=${location}`);
  },

  getChallenges: async (): Promise<Challenge[]> => {
    return apiRequest<Challenge[]>('/challenges');
  },

  startChallenge: async (challengeId: number) => {
    return apiRequest<{ message: string; user_challenge_id: number }>(`/start_challenge/${challengeId}`, {
      method: 'POST',
    });
  },

  getUserChallenges: async (): Promise<UserChallenge[]> => {
    return apiRequest<UserChallenge[]>('/user_challenges');
  },

  updateChallengeProgress: async (userChallengeId: number, progress: number) => {
    return apiRequest<{ message: string }>(`/update_challenge_progress/${userChallengeId}`, {
      method: 'PUT',
      body: JSON.stringify({ progress }),
    });
  },

  getConservationSummary: async (): Promise<ConservationSummary> => {
    return apiRequest<ConservationSummary>('/conservation_summary');
  },
};

// Society management API calls
export const societyAPI = {
  getSocietyDashboard: async (): Promise<SocietyDashboard> => {
    return apiRequest<SocietyDashboard>('/society_dashboard');
  },

  placeBulkOrder: async (orderData: {
    supplier_id: number;
    volume: number;
    price: number;
    society_id: number;
  }) => {
    return apiRequest<{ message: string; order_id: number }>('/society_bulk_order', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  },
};
