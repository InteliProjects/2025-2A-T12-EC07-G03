import React from 'react';
import { Header } from './Header';
import { RegisterForm } from '@/components/RegisterForm';

interface RegisterPageProps {
  onRegister?: (data: { name: string; email: string; password: string }) => void;
  onBackToLogin?: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onRegister, onBackToLogin }) => {
  const handleRegister = (data: { name: string; email: string; password: string }) => {
    console.log('Register data:', data);
    onRegister?.(data);
  };

  const handleBackToLogin = () => {
    console.log('Back to login');
    onBackToLogin?.();
  };

  return (
    <main className="w-full h-screen relative overflow-hidden bg-white flex flex-col">
      <img
        src="https://api.builder.io/api/v1/image/assets/TEMP/2af4e8c7bc894a18c56f75babe3775a97f5c46e1?width=2625"
        alt=""
        className="w-[800px] h-[1300px] rotate-0 shrink-0 opacity-95 backdrop-blur-[2px] absolute right-[-150px] top-[-150px] max-lg:w-[650px] max-lg:h-[1100px] max-lg:right-[-100px] max-md:w-[500px] max-md:h-[900px] max-md:right-[-50px] max-sm:hidden"
        role="presentation"
      />
      
      <Header />
      
      <RegisterForm 
        onSubmit={handleRegister}
        onBackToLogin={handleBackToLogin}
      />
    </main>
  );
};
