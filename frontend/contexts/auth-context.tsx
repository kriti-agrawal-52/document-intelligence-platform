'use client';

// Authentication context for Document Intelligence Platform
// Provides global authentication state and methods

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { authService } from '@/lib/auth-service';
import type {
  AuthState,
  UserProfileResponse,
  LoginRequest,
  UserCreate,
  UserProfileUpdate,
  PasswordChangeRequest
} from '@/lib/types';

// Auth action types
type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'LOGIN_SUCCESS'; payload: { user: UserProfileResponse; token: string } }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: UserProfileResponse }
  | { type: 'INITIALIZE_SUCCESS'; payload: UserProfileResponse }
  | { type: 'INITIALIZE_FAILURE' };

// Initial auth state
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  loading: true, // Start with loading true to check for existing auth
  error: null,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        token: action.payload.token,
        loading: false,
        error: null,
      };
    
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null,
      };
    
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
        error: null,
      };
    
    case 'INITIALIZE_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload,
        token: authService.getToken(),
        loading: false,
        error: null,
      };
    
    case 'INITIALIZE_FAILURE':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null,
      };
    
    default:
      return state;
  }
}

// Auth context type
interface AuthContextType {
  // State
  state: AuthState;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (profileData: UserProfileUpdate) => Promise<void>;
  changePassword: (passwordData: PasswordChangeRequest) => Promise<void>;
  deleteAccount: () => Promise<void>;
  clearError: () => void;
  
  // Utilities
  isAuthenticated: boolean;
  user: UserProfileResponse | null;
  loading: boolean;
  error: string | null;
}

// Create auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state from stored token
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const user = await authService.initializeAuth();
        if (user) {
          dispatch({ type: 'INITIALIZE_SUCCESS', payload: user });
        } else {
          dispatch({ type: 'INITIALIZE_FAILURE' });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        dispatch({ type: 'INITIALIZE_FAILURE' });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      const loginResponse = await authService.login(credentials);
      const user = await authService.getCurrentUser();

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user,
          token: loginResponse.access_token,
        },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  }, []);

  // Register function
  const register = useCallback(async (userData: UserCreate) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      await authService.register(userData);
      
      // Auto-login after successful registration
      await login({ username: userData.username, password: userData.password });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  }, [login]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await authService.logout();
      dispatch({ type: 'LOGOUT' });
    } catch (error) {
      // Even if logout fails on backend, clear local state
      dispatch({ type: 'LOGOUT' });
      console.error('Logout error:', error);
    }
  }, []);

  // Update profile function
  const updateProfile = useCallback(async (profileData: UserProfileUpdate) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const updatedUser = await authService.updateProfile(profileData);
      dispatch({ type: 'UPDATE_USER', payload: updatedUser });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Profile update failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  }, []);

  // Change password function
  const changePassword = useCallback(async (passwordData: PasswordChangeRequest) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      await authService.changePassword(passwordData);
      // Password change doesn't update user data, so no dispatch needed
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Password change failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  }, []);

  // Delete account function
  const deleteAccount = useCallback(async () => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      await authService.deleteAccount();
      dispatch({ type: 'LOGOUT' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Account deletion failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  }, []);

  // Clear error function
  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  // Context value
  const contextValue: AuthContextType = {
    // State
    state,
    
    // Actions
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    deleteAccount,
    clearError,
    
    // Utilities (derived from state)
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    loading: state.loading,
    error: state.error,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Custom hook for auth status only (optimized for components that only need auth status)
export function useAuthStatus() {
  const { isAuthenticated, loading, user } = useAuth();
  return { isAuthenticated, loading, user };
}

// Custom hook for auth actions only
export function useAuthActions() {
  const { login, register, logout, updateProfile, changePassword, deleteAccount, clearError } = useAuth();
  return { login, register, logout, updateProfile, changePassword, deleteAccount, clearError };
}
