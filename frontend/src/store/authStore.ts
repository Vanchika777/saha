import { create } from 'zustand';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthModalOpen: boolean;
  authModalMode: 'login' | 'register';
  setUser: (user: User | null, token?: string | null) => void;
  openAuthModal: (mode?: 'login' | 'register') => void;
  closeAuthModal: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('saha_token'),
  isAuthModalOpen: false,
  authModalMode: 'login',

  setUser: (user, token) => {
    if (token !== undefined) {
      if (token) {
        localStorage.setItem('saha_token', token);
      } else {
        localStorage.removeItem('saha_token');
      }
    }
    set({ user, token: token !== undefined ? token : localStorage.getItem('saha_token') });
  },

  openAuthModal: (mode = 'login') => set({ isAuthModalOpen: true, authModalMode: mode }),
  closeAuthModal: () => set({ isAuthModalOpen: false }),

  logout: () => {
    localStorage.removeItem('saha_token');
    set({ user: null, token: null });
  },
}));
