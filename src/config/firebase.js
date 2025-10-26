/**
 * Firebase Configuration
 * Initialize Firebase Authentication for admin panel
 */

import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, onAuthStateChanged } from 'firebase/auth';

// Firebase configuration
// TODO: Replace with your actual Firebase config
// Get from: https://console.firebase.google.com/ > Project Settings > General
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDemoKey123456789",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "highpal-demo.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "highpal-demo",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "highpal-demo.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "123456789",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:123456789:web:abc123"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Authorized admin emails (whitelist)
// TODO: Add your admin emails here
const AUTHORIZED_ADMINS = [
  'admin@highpal.com',
  'eddyutkarshteddy@gmail.com',
  // Add more admin emails
];

/**
 * Check if user is authorized admin
 */
export const isAuthorizedAdmin = (email) => {
  if (!email) return false;
  return AUTHORIZED_ADMINS.some(adminEmail => 
    email.toLowerCase() === adminEmail.toLowerCase()
  );
};

/**
 * Sign in with Google
 */
export const signInWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    
    // Check if user is authorized admin
    if (!isAuthorizedAdmin(user.email)) {
      await signOut(auth);
      throw new Error('Unauthorized: Only administrators can access this panel');
    }
    
    return { success: true, user };
  } catch (error) {
    console.error('Google sign-in error:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Sign in with email and password
 */
export const signInWithEmail = async (email, password) => {
  try {
    // Check if user is authorized admin
    if (!isAuthorizedAdmin(email)) {
      throw new Error('Unauthorized: Only administrators can access this panel');
    }
    
    const result = await signInWithEmailAndPassword(auth, email, password);
    return { success: true, user: result.user };
  } catch (error) {
    console.error('Email sign-in error:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Create admin account with email and password
 */
export const createAdminAccount = async (email, password) => {
  try {
    // Check if user is authorized admin
    if (!isAuthorizedAdmin(email)) {
      throw new Error('Unauthorized: Only whitelisted emails can create admin accounts');
    }
    
    const result = await createUserWithEmailAndPassword(auth, email, password);
    return { success: true, user: result.user };
  } catch (error) {
    console.error('Account creation error:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Sign out
 */
export const signOutUser = async () => {
  try {
    await signOut(auth);
    return { success: true };
  } catch (error) {
    console.error('Sign-out error:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Subscribe to auth state changes
 */
export const subscribeToAuthState = (callback) => {
  return onAuthStateChanged(auth, (user) => {
    if (user && isAuthorizedAdmin(user.email)) {
      callback({ user, isAdmin: true });
    } else {
      callback({ user: null, isAdmin: false });
    }
  });
};

export { auth };
