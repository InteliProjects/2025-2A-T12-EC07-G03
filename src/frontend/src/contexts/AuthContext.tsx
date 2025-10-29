import React, { createContext, useContext, useState, ReactNode } from 'react';
import { User } from '@/data/mockData';
import api from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      // Chamada real para a API de autenticação
      const response = await api.post('/auth/login', { email, password });
      
      if (response.data && response.data.user && response.data.token) {
        const userData: User = {
          id: response.data.user.id,
          name: response.data.user.name || response.data.user.email,
          email: response.data.user.email,
          avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(response.data.user.name || response.data.user.email)}&background=1934A5&color=fff`
        };
        
        setUser(userData);
        // Salvar token JWT e dados do usuário
        localStorage.setItem('auth_token', response.data.token);
        localStorage.setItem('user', JSON.stringify(userData));
        
        return { success: true };
      } else {
        return { success: false, error: 'Resposta inválida do servidor' };
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Erro ao fazer login. Verifique suas credenciais.';
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      setUser(null);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  };

  // Check for existing user on mount and validate token
  React.useEffect(() => {
    const initAuth = async () => {
      setInitializing(true);
      const savedUser = localStorage.getItem('user');
      const token = localStorage.getItem('auth_token');
      
      if (savedUser && token) {
        try {
          // Validar token com o backend
          const response = await api.get('/auth/me');
          
          if (response.data && response.data.user) {
            const userData: User = {
              id: response.data.user.id,
              name: response.data.user.name || response.data.user.email,
              email: response.data.user.email,
              avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(response.data.user.name || response.data.user.email)}&background=1934A5&color=fff`
            };
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
          } else {
            // Token inválido
            localStorage.removeItem('user');
            localStorage.removeItem('auth_token');
          }
        } catch (error) {
          // Token inválido ou erro de rede
          console.error('Erro ao validar token:', error);
          localStorage.removeItem('user');
          localStorage.removeItem('auth_token');
        }
      }
      setInitializing(false);
    };
    
    initAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading: loading || initializing
  };

  // Mostrar loading enquanto inicializa
  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#1934A5]"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};