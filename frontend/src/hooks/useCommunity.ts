import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAuthToken } from "@/services/api";

const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5001";

// --- Types ---
export interface Broadcast {
  id: number;
  title: string;
  content: string;
  created_at: string;
}

export interface Thread {
  id: number;
  title: string;
  content: string;
  category: string;
  author: string;
  created_at: string;
  comment_count: number;
}

export interface Comment {
  id: number;
  content: string;
  author: string;
  created_at: string;
}

// --- Fetcher Functions ---
const fetchWithAuth = async (endpoint: string) => {
  const token = getAuthToken();
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) throw new Error("Network response was not ok");
  return response.json();
};

const postWithAuth = async (endpoint: string, data: any) => {
  const token = getAuthToken();
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to post data");
  return response.json();
};

// --- Hooks ---
export function useBroadcasts() {
  return useQuery({
    queryKey: ["broadcasts"],
    queryFn: () => fetchWithAuth("/gamification/community/broadcasts"),
  });
}

export function useThreads() {
  return useQuery({
    queryKey: ["threads"],
    queryFn: () => fetchWithAuth("/gamification/community/threads"),
  });
}

export function useThreadComments(threadId: number | null) {
  return useQuery({
    queryKey: ["comments", threadId],
    queryFn: () => fetchWithAuth(`/gamification/community/threads/${threadId}/comments`),
    enabled: !!threadId,
  });
}

export function useCreateThread() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (newThread: { title: string; content: string; category: string }) =>
      postWithAuth("/gamification/community/threads", newThread),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["threads"] });
    },
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ threadId, content }: { threadId: number; content: string }) =>
      postWithAuth(`/gamification/community/threads/${threadId}/comments`, { content }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["comments", variables.threadId] });
      queryClient.invalidateQueries({ queryKey: ["threads"] });
    },
  });
}
