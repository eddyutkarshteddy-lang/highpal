# 🔥 Firebase Setup Guide for HighPal Admin Panel

## Quick Setup (Recommended)

### Option 1: Automated Setup Script
```powershell
# Run the setup script
.\setup-firebase.ps1
```
This interactive script will:
- Prompt for all Firebase credentials
- Update your `.env` file automatically
- Configure admin email whitelist
- Verify the setup

### Option 2: Manual Setup
Follow the steps below if you prefer manual configuration.

---

## Step-by-Step Manual Setup

### 1️⃣ Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or **"Create a project"**
3. Enter project name: `highpal-admin` (or your preferred name)
4. Disable Google Analytics (optional for admin panel)
5. Click **"Create project"**
6. Wait for project creation (~30 seconds)

### 2️⃣ Add Web App to Firebase

1. In your Firebase project overview, click the **`</>`** (Web) icon
2. Enter app nickname: **HighPal Admin Panel**
3. ✅ Check "Also set up Firebase Hosting" (optional)
4. Click **"Register app"**
5. Firebase will show your configuration object - **KEEP THIS PAGE OPEN**

Your config will look like this:
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef1234567890"
};
```

### 3️⃣ Enable Authentication Methods

#### Enable Google Sign-In:
1. In Firebase Console, go to **Build** → **Authentication**
2. Click **"Get started"** (if first time)
3. Go to **"Sign-in method"** tab
4. Click **"Google"** provider
5. Toggle **Enable** switch
6. Enter **Support email** (your email)
7. Click **"Save"**

#### Enable Email/Password:
1. Still in **"Sign-in method"** tab
2. Click **"Email/Password"** provider
3. Toggle **Enable** for "Email/Password"
4. Click **"Save"**

### 4️⃣ Configure Environment Variables

#### Edit `.env` file:
Open `c:\Users\eddyu\Documents\Projects\highpal\.env` and add/update:

```env
# Firebase Configuration (for Admin Authentication)
VITE_FIREBASE_API_KEY=your-api-key-from-step-2
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

**Copy each value from the Firebase config you got in Step 2.**

### 5️⃣ Add Admin Email Addresses

Edit `src/config/firebase.js` and update the whitelist:

```javascript
const AUTHORIZED_ADMINS = [
  'admin@highpal.com',
  'eddyutkarsh@gmail.com',
  'your-email@gmail.com',      // Add your Google account email
  'another-admin@domain.com',  // Add more as needed
];
```

**Important:** Only emails in this array can access the admin panel!

### 6️⃣ Verify Setup

Run the verification script:
```powershell
.\verify-firebase.ps1
```

This will check:
- ✓ `.env` file exists
- ✓ All Firebase variables are set
- ✓ Firebase SDK is installed
- ✓ Admin emails are configured

---

## Testing Firebase Authentication

### 1. Start Development Server
```powershell
npm run dev
```

### 2. Open Admin Login
Navigate to: http://localhost:5173/admin/login

### 3. Test Google Sign-In
1. Click **"Sign in with Google"**
2. Select your Google account
3. Grant permissions
4. You should be redirected to admin dashboard

**Troubleshooting:**
- If error: "Unauthorized domain" → Add `localhost` to authorized domains in Firebase Console
- If error: "Only administrators can access" → Check your email is in `AUTHORIZED_ADMINS` array

### 4. Test Email/Password
1. Click **"Don't have an account? Sign up"**
2. Enter email from `AUTHORIZED_ADMINS` list
3. Enter strong password
4. Click **"Sign Up"**
5. You should be redirected to admin dashboard

---

## Firebase Console Quick Links

After setup, bookmark these:

| Feature | URL |
|---------|-----|
| **Project Overview** | https://console.firebase.google.com/project/YOUR-PROJECT-ID/overview |
| **Authentication Users** | https://console.firebase.google.com/project/YOUR-PROJECT-ID/authentication/users |
| **Sign-in Methods** | https://console.firebase.google.com/project/YOUR-PROJECT-ID/authentication/providers |
| **Project Settings** | https://console.firebase.google.com/project/YOUR-PROJECT-ID/settings/general |

Replace `YOUR-PROJECT-ID` with your actual Firebase project ID.

---

## Security Configuration

### Add Authorized Domains (Production)

When deploying to production:

1. Go to **Authentication** → **Settings** → **Authorized domains**
2. Click **"Add domain"**
3. Add your production domain: `yourdomain.com`
4. Click **"Add"**

`localhost` is automatically authorized for development.

### Set Up Email Verification (Optional)

To require email verification:

1. Go to **Authentication** → **Templates**
2. Customize email verification template
3. Update code in `src/config/firebase.js`:
   ```javascript
   import { sendEmailVerification } from 'firebase/auth';
   
   export const createAdminAccount = async (email, password) => {
     const result = await createUserWithEmailAndPassword(auth, email, password);
     await sendEmailVerification(result.user);
     return { success: true, user: result.user };
   };
   ```

---

## Troubleshooting

### ❌ Error: "Firebase: Error (auth/configuration-not-found)"
**Solution:** Check your `.env` file has all Firebase variables set correctly.

### ❌ Error: "Firebase: Error (auth/api-key-not-valid)"
**Solution:** Your `VITE_FIREBASE_API_KEY` is incorrect. Copy it again from Firebase Console.

### ❌ Error: "Unauthorized: Only administrators can access this panel"
**Solution:** Your email is not in `AUTHORIZED_ADMINS` array. Add it to `src/config/firebase.js`.

### ❌ Error: "Firebase: Error (auth/unauthorized-domain)"
**Solution:** Add your domain to authorized domains in Firebase Console → Authentication → Settings.

### ❌ Google Sign-In popup blocked
**Solution:** Allow popups for localhost in your browser settings.

### ❌ Changes not reflected
**Solution:** Restart dev server after changing `.env`:
```powershell
# Stop server (Ctrl+C)
npm run dev
```

---

## Admin Panel Features After Setup

Once configured, you can:
- ✅ **Login** via Google or Email/Password
- ✅ **Upload** educational PDFs
- ✅ **Tag** content by exam type, subject, topic
- ✅ **Search** content with semantic search
- ✅ **Manage** uploaded content
- ✅ **View** analytics and statistics
- ✅ **Monitor** embeddings coverage

---

## Cost & Limits

Firebase Free Tier (Spark Plan):
- **Authentication:** 
  - Google Sign-In: Unlimited free
  - Email/Password: Unlimited free
- **Storage:** 1 GB
- **Downloads:** 10 GB/month

For HighPal admin panel with ~10 admins, you'll stay well within free tier.

**Upgrade to Blaze Plan (pay-as-you-go) only if:**
- You have 100+ admin users
- You need advanced security features
- You want custom domains

---

## Production Deployment

When ready for production:

1. **Update Firebase Authorized Domains:**
   - Add your production domain
   - Add any staging domains

2. **Set Environment Variables on Hosting:**
   - Vercel: Add env vars in project settings
   - Netlify: Add in Site settings → Build & deploy
   - Firebase Hosting: Use `.env.production`

3. **Enable Additional Security:**
   - Enable email verification
   - Set password strength requirements
   - Enable MFA (Multi-Factor Auth)

4. **Monitor Usage:**
   - Check Firebase Console → Usage dashboard
   - Set up budget alerts
   - Monitor authentication logs

---

## Quick Commands Reference

```powershell
# Setup Firebase (interactive)
.\setup-firebase.ps1

# Verify Firebase configuration
.\verify-firebase.ps1

# Start dev server
npm run dev

# Install Firebase (if needed)
npm install firebase

# Check Firebase version
npm list firebase
```

---

## Support

**Firebase Documentation:**
- [Authentication Guide](https://firebase.google.com/docs/auth/web/start)
- [Google Sign-In](https://firebase.google.com/docs/auth/web/google-signin)
- [Email/Password Auth](https://firebase.google.com/docs/auth/web/password-auth)

**HighPal Admin Panel:**
- Setup Guide: `ADMIN_PANEL_SETUP.md`
- Complete Guide: `ADMIN_PANEL_COMPLETE.md`

---

## Next Steps

After Firebase is configured:
1. ✅ Test admin login flow
2. ✅ Upload sample PDF content
3. ✅ Test search functionality
4. ✅ Verify embeddings generation
5. ⏭️ Connect to "Learn with Pal" mode (query routing)

**Your admin panel is now fully secured with Firebase! 🎉**
