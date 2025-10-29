import React from 'react';
import { Navigate } from 'react-router-dom';
import { Dashboard as DashboardComponent } from '@/components/Dashboard';
import { useAuth } from '@/contexts/AuthContext';

const DashboardPage = () => {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleLogout = async () => {
    await logout();
  };

  return (
    <DashboardComponent 
      user={user} 
      onLogout={handleLogout} 
    />
  );
};

export default DashboardPage;