import React from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { RegisterPage } from '@/components/RegisterPage';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import api from '@/lib/api';

const Register = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleRegister = async (data: { name: string; email: string; password: string }) => {
    try {
      const response = await api.post('/auth/register', data);

      if (response.data) {
        toast.success('Cadastro realizado com sucesso! Faça login para continuar.');
        // Redirecionar para login
        navigate('/');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Erro ao fazer cadastro. Tente novamente.';
      toast.error(errorMessage);
    }
  };

  const handleBackToLogin = () => {
    navigate('/');
  };

  return (
    <RegisterPage 
      onRegister={handleRegister}
      onBackToLogin={handleBackToLogin}
    />
  );
};

export default Register;
