# 🎯 Admin Panel Setup Guide

## ✅ What Was Implemented

A complete admin panel with Firebase authentication for managing educational content.

### Features
- 🔐 **Firebase Authentication** (Google Sign-In + Email/Password)
- 📤 **Content Upload** (PDF files, URLs, bulk URLs)
- 🏷️ **Tagging System** (Exam type, subject, topic, difficulty, etc.)
- 📚 **Content Management** (Search, filter, semantic/keyword search)
- 📊 **Statistics Dashboard** (Embeddings status, content analytics)
- 🔒 **Protected Routes** (Admin-only access)

## 📁 Files Created

### Authentication
- `src/config/firebase.js` - Firebase configuration and auth methods
- `src/contexts/AuthContext.jsx` - Auth state management
- `src/components/ProtectedRoute.jsx` - Route protection wrapper

### Admin Components
- `src/components/AdminLogin.jsx` + `.css` - Login page
- `src/components/AdminDashboard.jsx` + `.css` - Main dashboard
- `src/components/ContentUpload.jsx` + `.css` - Upload interface
- `src/components/ContentManagement.jsx` + `.css` - Content browser
- `src/components/StatisticsDashboard.jsx` + `.css` - Analytics

### Routing
- `src/AppRouter.jsx` - Routes for student portal + admin panel
- `src/main.jsx` - Updated to use router

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Already installed: firebase, react-router-dom
npm install
```

### 2. Start the Application
```bash
npm run dev
```

### 3. Access Admin Panel
Navigate to: **http://localhost:5173/admin/login**

### 4. Login Credentials

**For Development (Mock Mode):**
- Use any email from the whitelist in `src/config/firebase.js`
- Default: `admin@highpal.com` or `eddyutkarsh@gmail.com`
- Password: any (will work in demo mode if Firebase not configured)

**With Real Firebase:**
1. Set up Firebase project
2. Add credentials to `.env` file
3. Enable Google Sign-In in Firebase Console
4. Create admin accounts with whitelisted emails

## 🔧 Configuration

### Firebase Setup (Optional for Testing)

1. **Create Firebase Project**
   - Go to https://console.firebase.google.com/
   - Create new project
   - Enable Authentication → Google Sign-In

2. **Get Configuration**
   - Project Settings → General
   - Copy web app config values

3. **Update `.env` file**
   ```env
   VITE_FIREBASE_API_KEY=your-key
   VITE_FIREBASE_AUTH_DOMAIN=your-domain
   VITE_FIREBASE_PROJECT_ID=your-project
   VITE_FIREBASE_STORAGE_BUCKET=your-bucket
   VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   VITE_FIREBASE_APP_ID=your-app-id
   ```

4. **Add Admin Emails**
   - Edit `src/config/firebase.js`
   - Update `AUTHORIZED_ADMINS` array with your admin emails

### Backend API Configuration

Make sure backend is running:
```bash
cd backend
python training_server.py
```

API should be available at: `http://localhost:8003`

## 🎨 Admin Panel Features

### 1. Content Upload Tab

**File Upload:**
- Drag & drop or click to select PDF
- Add tags (exam type, subject, topic, etc.)
- Automatic embedding generation
- Progress tracking

**URL Upload:**
- Paste public PDF URL
- Same tagging system
- Downloads and processes automatically

**Bulk Upload:**
- Multiple URLs (one per line)
- Same tags applied to all
- Batch processing

**Required Tags:**
- ✅ Exam Type(s) - at least one (JEE, NEET, CAT, etc.)
- ✅ Subject - required
- ⚪ Topic, Chapter - optional
- ⚪ Difficulty - default: intermediate
- ⚪ Class, Language - optional

### 2. Content Management Tab

**Search Features:**
- 🧠 Semantic search (uses vector embeddings)
- 🔤 Keyword search (fallback)
- Filter by exam type
- Filter by subject

**Results Display:**
- Similarity scores
- Content preview
- Source information
- Chunk details
- Embedding status

### 3. Statistics Dashboard

**Metrics:**
- Total documents
- Embeddings coverage (%)
- Content by exam type
- Content by subject
- Available tags

**Actions:**
- Refresh statistics
- Regenerate embeddings (for content without embeddings)
- View coverage progress bar

## 📱 User Flow

### Admin Login Flow
1. Navigate to `/admin/login`
2. Choose sign-in method:
   - Google Sign-In (recommended)
   - Email/Password
3. System checks if email is whitelisted
4. Redirect to dashboard if authorized
5. Show error if not whitelisted

### Content Upload Flow
1. Select upload method (File/URL/Bulk)
2. Choose file or enter URL(s)
3. Fill required tags (exam type, subject)
4. Add optional tags (topic, difficulty, etc.)
5. Click "Upload"
6. Watch progress bar
7. See success message with chunk count
8. Embeddings generated automatically

### Content Search Flow
1. Go to "Manage Content" tab
2. Enter search query
3. Choose filters (exam, subject)
4. Select search method (semantic/keyword)
5. Click "Search"
6. View results with similarity scores
7. Browse content details

## 🔒 Security Features

### Authorization
- **Whitelist-based**: Only pre-approved emails can access
- **Protected routes**: All admin routes require authentication
- **Session persistence**: Stay logged in across page refreshes
- **Auto-logout**: Unauthorized users redirected to login

### Configuration
Add admin emails in `src/config/firebase.js`:
```javascript
const AUTHORIZED_ADMINS = [
  'admin@highpal.com',
  'eddyutkarsh@gmail.com',
  'your-email@domain.com',  // Add your email here
];
```

## 🎯 Routes

### Student Portal
- `/` - Main student interface
- `/student/*` - Student features

### Admin Panel
- `/admin/login` - Login page (public)
- `/admin/dashboard` - Admin dashboard (protected)
- `/admin` - Redirects to dashboard

### Protection
All `/admin/*` routes except `/admin/login` require authentication.

## 🧪 Testing the Admin Panel

### Test 1: Login Flow
```
1. Open http://localhost:5173/admin/login
2. Try Google Sign-In (will show Firebase demo message)
3. Try email login with admin@highpal.com + any password
4. Should redirect to dashboard
```

### Test 2: Upload Content
```
1. Go to "Upload Content" tab
2. Select a test PDF file
3. Choose exam type: JEE
4. Enter subject: Physics
5. Click "Upload"
6. Check for success message
7. Verify embeddings were generated
```

### Test 3: Search Content
```
1. Go to "Manage Content" tab
2. Enter query: "thermodynamics"
3. Select semantic search
4. Click "Search"
5. Verify results appear
6. Check similarity scores
```

### Test 4: View Statistics
```
1. Go to "Statistics" tab
2. Check embeddings status
3. View content by exam type chart
4. View content by subject chart
5. Check coverage percentage
```

## 🐛 Troubleshooting

### Issue: Can't access admin panel
**Solution:** Check if email is in `AUTHORIZED_ADMINS` array

### Issue: Firebase errors
**Solution:** Either configure Firebase or ignore (works in demo mode)

### Issue: Upload fails
**Solution:** Ensure backend is running on port 8003

### Issue: Search returns no results
**Solution:** Upload some content first or check backend logs

### Issue: Embeddings not working
**Solution:** Check `OPENAI_API_KEY` in backend `.env`

## 🎨 Customization

### Change Admin Emails
Edit `src/config/firebase.js`:
```javascript
const AUTHORIZED_ADMINS = [
  'your-email@domain.com',
  // add more emails
];
```

### Change Backend URL
Edit API_BASE in components:
```javascript
const API_BASE = 'http://your-backend-url:port';
```

### Modify UI Colors
Edit component CSS files to change gradient colors:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Add More Exam Types
Edit `ContentUpload.jsx`:
```javascript
const EXAM_TYPES = ['JEE', 'NEET', 'NEW_EXAM', ...];
```

## 📊 Next Steps

1. ✅ **Admin Panel Complete**
2. ⏭️ **Connect to "Learn with Pal" mode** (Query routing)
3. ⏭️ **Add video support** (YouTube transcripts)
4. ⏭️ **Production deployment** (Firebase hosting)
5. ⏭️ **Enhanced features** (Edit/delete content, user management)

## 💡 Tips

- **Test with real PDFs**: Upload JEE/NEET study materials
- **Use semantic search**: Much better than keyword search
- **Monitor embeddings**: Keep coverage at 100% for best results
- **Bulk upload**: Faster for multiple files with same tags
- **Tag consistently**: Use same subject/topic names for better filtering

## 📞 Support

- **Frontend**: Check browser console for errors
- **Backend**: Check `backend/logs/` folder
- **Firebase**: Check Firebase Console → Authentication
- **API**: Test endpoints at `http://localhost:8003/docs`

## 🎉 Success!

Your admin panel is ready! You can now:
- ✅ Log in as admin
- ✅ Upload educational content
- ✅ Tag content for organization
- ✅ Search with semantic understanding
- ✅ Monitor analytics and embeddings
- ✅ Manage knowledge base for students
