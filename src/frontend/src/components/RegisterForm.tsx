import React, { useState } from 'react';
import { useForm } from 'react-hook-form';

interface RegisterFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface RegisterFormProps {
  onSubmit?: (data: Omit<RegisterFormData, 'confirmPassword'>) => void;
  onBackToLogin?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSubmit, onBackToLogin }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterFormData>({
    defaultValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: ''
    }
  });

  const password = watch('password');

  const handleFormSubmit = (data: RegisterFormData) => {
    console.log('Register attempt:', data);
    const { confirmPassword, ...registerData } = data;
    onSubmit?.(registerData);
  };

  const handleBackToLogin = () => {
    console.log('Back to login clicked');
    onBackToLogin?.();
  };

  return (
    <div className="container max-w-lg mx-0 ml-16 px-0 pt-32 max-lg:ml-12 max-lg:pt-28 max-md:ml-8 max-md:pt-24 max-sm:ml-6 max-sm:pt-20">
      <h2 className="text-[#1934A5] text-3xl font-bold mb-8 max-lg:text-2xl max-lg:mb-6 max-md:text-xl max-md:mb-5 max-sm:text-lg max-sm:mb-4">
        SyncTelemetry
      </h2>
      
      <p className="text-[rgba(0,0,0,0.60)] text-base font-normal mb-6 max-md:text-sm max-md:mb-4 max-sm:text-xs max-sm:mb-3">
        Crie sua conta!
      </p>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5 max-w-md">
        <div className="relative">
          <div className="w-full h-14 border relative bg-white border-solid border-[#C1BBBB] max-md:h-12 max-sm:h-10">
            <div className="w-12 h-0 absolute bg-[#1934A5] left-1.5 top-px" />
            <label 
              htmlFor="name"
              className="text-[rgba(0,0,0,0.61)] text-sm font-normal absolute left-4 top-2 max-sm:text-xs max-sm:left-3 max-sm:top-1"
            >
              Nome completo
            </label>
            <input
              id="name"
              type="text"
              placeholder="João Silva"
              {...register('name', { 
                required: 'Nome é obrigatório',
                minLength: {
                  value: 3,
                  message: 'Nome deve ter pelo menos 3 caracteres'
                }
              })}
              className="text-[#1934A5] text-sm font-normal absolute left-4 top-7 max-sm:text-xs max-sm:left-3 max-sm:top-5 bg-transparent border-none outline-none w-[calc(100%-32px)]"
              aria-describedby={errors.name ? 'name-error' : undefined}
            />
            {errors.name && (
              <span id="name-error" className="text-red-500 text-xs absolute left-4 top-full mt-1 max-sm:left-3">
                {errors.name.message}
              </span>
            )}
          </div>
        </div>

        <div className="relative">
          <div className="w-full h-14 border relative bg-white border-solid border-[#C1BBBB] max-md:h-12 max-sm:h-10">
            <div className="w-12 h-0 absolute bg-[#1934A5] left-1.5 top-px" />
            <label 
              htmlFor="email"
              className="text-[rgba(0,0,0,0.61)] text-sm font-normal absolute left-4 top-2 max-sm:text-xs max-sm:left-3 max-sm:top-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="grupo03@inteli.edu.br"
              {...register('email', { 
                required: 'Email é obrigatório',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Email inválido'
                }
              })}
              className="text-[#1934A5] text-sm font-normal absolute left-4 top-7 max-sm:text-xs max-sm:left-3 max-sm:top-5 bg-transparent border-none outline-none w-[calc(100%-32px)]"
              aria-describedby={errors.email ? 'email-error' : undefined}
            />
            {errors.email && (
              <span id="email-error" className="text-red-500 text-xs absolute left-4 top-full mt-1 max-sm:left-3">
                {errors.email.message}
              </span>
            )}
          </div>
        </div>

        <div className="relative">
          <div className="w-full h-14 border relative bg-white border-solid border-[#C1BBBB] max-md:h-12 max-sm:h-10">
            <label 
              htmlFor="password"
              className="text-[rgba(0,0,0,0.61)] text-sm font-normal absolute left-4 top-2 max-sm:text-xs max-sm:left-3 max-sm:top-1"
            >
              Senha
            </label>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              {...register('password', { 
                required: 'Senha é obrigatória',
                minLength: {
                  value: 8,
                  message: 'Senha deve ter pelo menos 8 caracteres'
                }
              })}
              className="text-[#1934A5] text-sm font-normal absolute left-4 top-7 max-sm:text-xs max-sm:left-3 max-sm:top-5 bg-transparent border-none outline-none w-[calc(100%-32px)]"
              placeholder="*******************"
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            {errors.password && (
              <span id="password-error" className="text-red-500 text-xs absolute left-4 top-full mt-1 max-sm:left-3">
                {errors.password.message}
              </span>
            )}
          </div>
        </div>

        <div className="relative">
          <div className="w-full h-14 border relative bg-white border-solid border-[#C1BBBB] max-md:h-12 max-sm:h-10">
            <label 
              htmlFor="confirmPassword"
              className="text-[rgba(0,0,0,0.61)] text-sm font-normal absolute left-4 top-2 max-sm:text-xs max-sm:left-3 max-sm:top-1"
            >
              Confirmar senha
            </label>
            <input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              {...register('confirmPassword', { 
                required: 'Confirmação de senha é obrigatória',
                validate: (value) => value === password || 'As senhas não coincidem'
              })}
              className="text-[#1934A5] text-sm font-normal absolute left-4 top-7 max-sm:text-xs max-sm:left-3 max-sm:top-5 bg-transparent border-none outline-none w-[calc(100%-32px)]"
              placeholder="*******************"
              aria-describedby={errors.confirmPassword ? 'confirmPassword-error' : undefined}
            />
            {errors.confirmPassword && (
              <span id="confirmPassword-error" className="text-red-500 text-xs absolute left-4 top-full mt-1 max-sm:left-3">
                {errors.confirmPassword.message}
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-4 max-sm:flex-col max-sm:gap-3">
          <button
            type="submit"
            className="w-28 h-11 shadow-[0_4px_3px_0_rgba(0,0,0,0.25)] flex items-center justify-center cursor-pointer bg-[#1934A5] max-sm:w-full max-sm:h-9 hover:bg-[#152a85] transition-colors"
          >
            <span className="text-white text-sm font-normal max-sm:text-xs">
              Cadastrar
            </span>
          </button>
          <button
            type="button"
            onClick={handleBackToLogin}
            className="w-28 h-11 border flex items-center justify-center cursor-pointer bg-white border-solid border-[#1934A5] max-sm:w-full max-sm:h-9 hover:bg-[#f8f9ff] transition-colors"
          >
            <span className="text-[#1934A5] text-sm font-bold max-sm:text-xs">
              Voltar
            </span>
          </button>
        </div>
      </form>
    </div>
  );
};
