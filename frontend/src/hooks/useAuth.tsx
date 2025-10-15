'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { User, LoginRequest } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  setupRequired: boolean;
  initialSetup: (credentials: LoginRequest) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [setupRequired, setSetupRequired] = useState(false);
  const queryClient = useQueryClient();
  const router = useRouter();

  // Check if user is authenticated
  const { data: currentUser, isLoading: userLoading, error } = useQuery(
    'currentUser',
    apiClient.getCurrentUser,
    {
      enabled: !!Cookies.get('access_token'),
      retry: false,
      onError: () => {
        Cookies.remove('access_token');
        setUser(null);
      },
    }
  );

  // Check setup status
  const { data: setupStatus } = useQuery(
    'setupStatus',
    apiClient.setupStatus,
    {
      retry: false,
    }
  );

  useEffect(() => {
    if (currentUser) {
      setUser(currentUser);
    }
    setIsLoading(userLoading);
  }, [currentUser, userLoading]);

  useEffect(() => {
    if (setupStatus) {
      setSetupRequired(setupStatus.setup_required);
    }
  }, [setupStatus]);

  const loginMutation = useMutation(apiClient.login, {
    onSuccess: (data) => {
      Cookies.set('access_token', data.access_token, {
        expires: 1, // 1 day
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
      });
      setUser(data.user);
      queryClient.invalidateQueries('currentUser');
      toast.success('Erfolgreich angemeldet');
      router.push('/');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Anmeldung fehlgeschlagen');
    },
  });

  const logoutMutation = useMutation(apiClient.logout, {
    onSuccess: () => {
      Cookies.remove('access_token');
      setUser(null);
      queryClient.clear();
      toast.success('Erfolgreich abgemeldet');
      router.push('/login');
    },
    onError: () => {
      // Even if logout fails on server, clear local state
      Cookies.remove('access_token');
      setUser(null);
      queryClient.clear();
      router.push('/login');
    },
  });

  const setupMutation = useMutation(apiClient.initialSetup, {
    onSuccess: (data) => {
      Cookies.set('access_token', data.access_token, {
        expires: 1,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
      });
      setUser(data.user);
      setSetupRequired(false);
      queryClient.invalidateQueries('setupStatus');
      queryClient.invalidateQueries('currentUser');
      toast.success('Setup abgeschlossen');
      router.push('/');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Setup fehlgeschlagen');
    },
  });

  const login = async (credentials: LoginRequest) => {
    await loginMutation.mutateAsync(credentials);
  };

  const logout = async () => {
    await logoutMutation.mutateAsync();
  };

  const initialSetup = async (credentials: LoginRequest) => {
    await setupMutation.mutateAsync(credentials);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    login,
    logout,
    setupRequired,
    initialSetup,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
