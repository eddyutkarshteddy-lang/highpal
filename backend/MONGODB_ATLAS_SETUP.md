# MongoDB Atlas Configuration for HighPal

## 🚀 Setup Instructions

### 1. Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Sign up for a free account
3. Create a new project (e.g., "HighPal")
4. Create a new cluster (M0 Free tier)

### 2. Get Connection String
1. In your cluster, click "Connect"
2. Choose "Connect your application"
3. Copy the connection string (it looks like):
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 3. Configure Environment
1. Open `backend/.env` file
2. Add your MongoDB connection string:
   ```env
   MONGODB_URI=mongodb+srv://your_username:your_password@cluster0.xxxxx.mongodb.net/highpal?retryWrites=true&w=majority
   STORAGE_TYPE=mongodb
   ```

### 4. Database Structure
Your documents will be stored in:
- **Database**: `highpal`
- **Collection**: `documents`

### 5. Start the Server
```bash
cd backend
python mongodb_server.py
```

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb+srv://...` |
| `STORAGE_TYPE` | Storage backend type | `mongodb` |
| `DATABASE_NAME` | MongoDB database name | `highpal` |
| `COLLECTION_NAME` | MongoDB collection name | `documents` |

## 📊 Features with MongoDB

✅ **Cloud Storage** - All documents stored in MongoDB Atlas  
✅ **Automatic Backups** - Atlas provides automated backups  
✅ **Scalable** - Grows with your data needs  
✅ **Global Access** - Access from anywhere  
✅ **Search Indexing** - Built-in search capabilities  
✅ **Local Fallback** - Falls back to local storage if MongoDB is unavailable  

## 🛠️ Troubleshooting

### Connection Issues
- Check your IP address is whitelisted in Atlas
- Verify username/password in connection string
- Ensure cluster is active

### Firewall Issues
- Add your IP to Atlas IP whitelist
- Or use `0.0.0.0/0` for all IPs (less secure)

### Authentication Issues
- Double-check username and password
- Make sure user has read/write permissions
