'use client';

import { ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Navigation from './Navigation';

interface LayoutProps {
  children: ReactNode;
  requireAuth?: boolean;
  requireAdmin?: boolean;
}

export default function Layout({ 
  children, 
  requireAuth = true, 
  requireAdmin = false 
}: LayoutProps) {
  const { isAuthenticated, isAdmin, isLoading, setupRequired } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (setupRequired && requireAuth) {
        router.push('/setup');
        return;
      }

      if (requireAuth && !isAuthenticated) {
        router.push('/login');
        return;
      }

      if (requireAdmin && !isAdmin) {
        router.push('/');
        return;
      }
    }
  }, [isLoading, isAuthenticated, isAdmin, setupRequired, requireAuth, requireAdmin, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    return null; // Will redirect to login
  }

  if (requireAdmin && !isAdmin) {
    return null; // Will redirect to home
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
