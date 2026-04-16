/**
 * Zustand stores — global state management.
 * Auth store: JWT + user info
 * Profile store: financial profile data for the current user
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── Auth Store ──
interface AuthState {
  token: string | null;
  user: { id: string; email: string; full_name: string } | null;
  isAuthenticated: boolean;
  login: (token: string, user: { id: string; email: string; full_name: string }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token, user) => {
        localStorage.setItem("access_token", token);
        set({ token, user, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem("access_token");
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    { name: "auth-storage" }
  )
);

// ── Financial Profile Store ──
interface FinancialProfile {
  netWorth: number;
  totalAssets: number;
  totalLiabilities: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  emergencyFundMonths: number;
  riskScore: number;
  riskCategory: string;
}

interface ProfileState {
  profile: FinancialProfile;
  isLoaded: boolean;
  setProfile: (p: Partial<FinancialProfile>) => void;
  reset: () => void;
}

const defaultProfile: FinancialProfile = {
  netWorth: 0,
  totalAssets: 0,
  totalLiabilities: 0,
  monthlyIncome: 0,
  monthlyExpenses: 0,
  emergencyFundMonths: 0,
  riskScore: 0,
  riskCategory: "unknown",
};

export const useProfileStore = create<ProfileState>()((set) => ({
  profile: defaultProfile,
  isLoaded: false,
  setProfile: (p) =>
    set((state) => ({
      profile: { ...state.profile, ...p },
      isLoaded: true,
    })),
  reset: () => set({ profile: defaultProfile, isLoaded: false }),
}));

// ── UI Store ──
interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
