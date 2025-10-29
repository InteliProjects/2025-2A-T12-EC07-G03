import React from 'react';
import { Header } from './Header';
import { LoginForm } from './LoginForm';

interface LoginPageProps {
  onLogin?: (data: { email: string; password: string; remember: boolean }) => void;
  onRegister?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onRegister }) => {
  const handleLogin = (data: { email: string; password: string; remember: boolean }) => {
    // Here you would typically make an API call to authenticate the user
    console.log('Login data:', data);
    onLogin?.(data);
  };

  const handleRegister = () => {
    // Here you would typically navigate to a registration page
    console.log('Navigate to register');
    onRegister?.(
    );
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
      
      <LoginForm 
        onSubmit={handleLogin}
        onRegister={handleRegister}
      />
    </main>
  );
};
