import React from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { LoginPage } from '@/components/LoginPage';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';

const Index = () => {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleLogin = async (data: { email: string; password: string; remember: boolean }) => {
    const result = await login(data.email, data.password);
    
    if (result.success) {
      toast.success('Login realizado com sucesso!');
      // Navigation will happen automatically via the Navigate component above
    } else {
      toast.error(result.error || 'Erro ao fazer login');
    }
  };

  const handleRegister = () => {
    navigate('/register');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1934A5]"></div>
      </div>
    );
  }

  return (
    <LoginPage 
      onLogin={handleLogin}
      onRegister={handleRegister}
    />
  );
};

export default Index;
