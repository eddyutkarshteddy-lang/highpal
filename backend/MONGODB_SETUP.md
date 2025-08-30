# 🚀 MongoDB Atlas Setup Guide for HighPal

## Quick Start with MongoDB Atlas (Free Tier)

### Step 1: Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Click "Try Free" and create an account
3. Verify your email address

### Step 2: Create a Cluster
1. Choose "Build a Database"
2. Select **M0 Sandbox** (Free tier)
3. Choose your preferred cloud provider and region
4. Name your cluster (e.g., "highpal-cluster")
5. Click "Create Cluster"

### Step 3: Create Database User
1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Create a username and password (save these!)
5. Set privileges to "Atlas Admin" or "Read and write to any database"
6. Click "Add User"

### Step 4: Configure Network Access
1. Go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. For development, click "Allow Access from Anywhere" (0.0.0.0/0)
4. For production, add your specific IP addresses
5. Click "Confirm"

### Step 5: Get Connection String
1. Go to "Clusters" (Database Deployments)
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Select "Python" and version "3.6 or later"
5. Copy the connection string (it looks like):
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 6: Configure HighPal
Choose **ONE** of these methods:

#### Method A: Environment Variable (Recommended)
Open PowerShell and run:
```powershell
$env:MONGODB_URI="mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
```

#### Method B: .env File
1. Copy `.env.example` to `.env` in the backend directory:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Edit `.env` file and uncomment the MONGODB_URI line:
   ```
   MONGODB_URI=mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

**Important:** Replace `your-username` and `your-password` with your actual database credentials!

### Step 7: Start the Enhanced Server
```powershell
python mongodb_server.py
```

You should see:
```
✅ MongoDB Atlas: CONFIGURED
☁️ Storage: Cloud (MongoDB Atlas)
```

## Verification

1. Visit http://localhost:8002/admin - Should show "MongoDB Atlas" storage
2. Visit http://localhost:8002/health - Should show connection status
3. Visit http://localhost:8002/setup - Should show configuration status

## Testing Upload

Upload a PDF or add a document - it will now be saved to MongoDB Atlas in the cloud!

## Troubleshooting

### Connection Issues
- Check your username/password in the connection string
- Verify network access allows your IP
- Make sure cluster is active (not paused)

### Authentication Errors
- Double-check username and password
- Ensure user has correct permissions
- Try recreating the database user

### Network Errors
- Check if 0.0.0.0/0 is in Network Access
- Try adding your specific IP address
- Verify firewall isn't blocking connections

## Features with MongoDB Atlas

✅ **Cloud Storage** - Documents saved in MongoDB Atlas
✅ **Automatic Backup** - Falls back to local storage if needed  
✅ **Scalable** - Handles large document collections
✅ **Searchable** - Fast document retrieval and search
✅ **Secure** - MongoDB Atlas encryption and security
✅ **Free Tier** - 512 MB storage included

## API Endpoints

All existing endpoints now support cloud storage:
- `POST /upload_pdf` - Upload PDFs to cloud
- `POST /url` - Save web content to cloud  
- `POST /documents` - Add documents to cloud
- `GET /documents` - Retrieve from cloud
- `DELETE /documents/{id}` - Delete from cloud

## Need Help?

- Visit `/setup` endpoint for live configuration status
- Check `/health` endpoint for connection diagnostics
- Review logs for detailed error messages

Happy cloud storing! 🎉
