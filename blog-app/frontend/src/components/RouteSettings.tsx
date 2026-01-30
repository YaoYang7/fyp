import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '../store/hooks';

interface RouteProtectionProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute - Requires user to be authenticated
 * Redirects to /home if not logged in
 */
export const ProtectedRoute: React.FC<RouteProtectionProps> = ({ children }) => {
  const { isLoggedIn } = useAppSelector((state) => state.auth);

  if (!isLoggedIn) {
    return <Navigate to="/home" replace />;
  }

  return <>{children}</>;
};

/**
 * GuestRoute - Requires user to NOT be authenticated
 * Redirects to /dashboard if already logged in
 */
export const GuestRoute: React.FC<RouteProtectionProps> = ({ children }) => {
  const { isLoggedIn } = useAppSelector((state) => state.auth);

  if (isLoggedIn) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
