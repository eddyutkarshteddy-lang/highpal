/**
 * Authentication Context
 * Manages authentication state across the application
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { subscribeToAuthState, signOutUser } from '../config/firebase';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Subscribe to auth state changes
    const unsubscribe = subscribeToAuthState(({ user, isAdmin }) => {
      setCurrentUser(user);
      setIsAdmin(isAdmin);
      setLoading(false);
    });

    // Cleanup subscription
    return unsubscribe;
  }, []);

  const logout = async () => {
    const result = await signOutUser();
    if (result.success) {
      setCurrentUser(null);
      setIsAdmin(false);
    }
    return result;
  };

  const value = {
    currentUser,
    isAdmin,
    loading,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
