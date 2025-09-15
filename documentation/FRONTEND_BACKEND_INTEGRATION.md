# 🔗 Frontend-Backend Integration Guide

This guide walks you through connecting your Next.js frontend to your Document Intelligence microservices backend.

## 📋 What's Been Implemented

### ✅ Backend API Integration Layer

- **`frontend/lib/api.ts`** - Complete API service with all backend endpoints
- **`frontend/contexts/auth-context.tsx`** - Authentication state management
- **JWT token management** - Automatic token storage and refresh
- **Error handling** - Comprehensive error handling for all API calls
- **TypeScript types** - Fully typed API responses and requests

### ✅ Updated Frontend Components

- **Login Form** - Now connects to `POST /auth/token`
- **Registration Form** - Now connects to `POST /auth/register`
- **Document List** - Now fetches from `GET /extract/documents`
- **Document Upload** - Now uploads to `POST /extract/image_text`
- **Authentication Guards** - Protected routes with automatic redirects

### ✅ Backend Endpoints Added

- **`GET /extract/documents`** - List all user documents (sorted by date)

## 🚀 Setup Instructions

### Step 1: Create Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 3: Start Backend Services

In separate terminals:

```bash
# Terminal 1: Auth Service
cd auth_service
python main.py

# Terminal 2: Text Extraction Service
cd text_extraction_service
python main.py

# Terminal 3: Text Summarization Service (optional)
cd text_summarization_service
python main.py
```

### Step 4: Test API Connectivity

```bash
cd frontend
node test-api.js
```

You should see:

```
🧪 Testing Document Intelligence API...
✅ Auth service health: Auth Service is healthy!
✅ Text extraction service health: Text Extraction Service is healthy!
✅ All API endpoints are accessible!
```

### Step 5: Start Frontend

```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000`

## 🔄 User Flow

### 1. **Landing Page** (`/`)

- Beautiful landing page with login form
- Features overview
- Registration link

### 2. **Registration** (`/register`)

- Create new account
- Real-time username validation
- Password strength indicator
- Automatic login after registration

### 3. **Dashboard** (`/dashboard`)

- Welcome message with user info
- Recent documents list
- Quick upload zone
- Navigation to all features

### 4. **Document Upload** (`/dashboard/upload`)

- Drag & drop file upload
- Real-time progress tracking
- Automatic text extraction
- Success/error handling

### 5. **Document Management** (`/dashboard/documents`)

- List all user documents
- Filter by status (completed/processing/failed)
- Sort by date, name, status
- View document details

### 6. **Document Details** (`/dashboard/documents/[id]`)

- View extracted text
- View AI-generated summary
- Copy to clipboard functionality
- File metadata

## 🔧 API Endpoints Used

### Authentication

```typescript
POST / auth / register; // User registration
POST / auth / token; // User login
GET / auth / users / me; // Get current user info
```

### Documents

```typescript
GET / extract / documents; // List user documents
POST / extract / image_text; // Upload document
GET / extract / document / { name }; // Get document details
```

## 🔐 Authentication Flow

1. **Login/Register** → JWT token received
2. **Token Storage** → Stored in localStorage
3. **API Requests** → Token included in Authorization header
4. **Token Validation** → Backend validates token
5. **Auto Logout** → Invalid/expired tokens trigger logout

## 📱 Features Implemented

### ✅ Core Features

- ✅ User registration and login
- ✅ JWT authentication
- ✅ Document upload with progress
- ✅ Document listing (sorted by date)
- ✅ Document details viewing
- ✅ Text extraction results
- ✅ AI summary viewing
- ✅ Responsive design
- ✅ Error handling
- ✅ Loading states
- ✅ Toast notifications

### 🔄 Processing States

- **Uploading** - File upload progress
- **Processing** - AI text extraction in progress
- **Completed** - Text extracted and summary generated
- **Failed** - Error in processing

## 🎨 UI/UX Features

### Design System

- **Modern Blue Theme** - Professional color scheme
- **Responsive Layout** - Desktop-first, mobile-friendly
- **Component Library** - Radix UI + Tailwind CSS
- **Consistent Spacing** - Grid-based layout system
- **Smooth Animations** - Loading states and transitions

### User Experience

- **Real-time Feedback** - Toast notifications for all actions
- **Loading States** - Progress indicators and skeleton screens
- **Error Recovery** - Clear error messages with retry options
- **Intuitive Navigation** - Breadcrumbs and clear CTAs

## 🧪 Testing the Integration

### Test User Registration

1. Go to `/register`
2. Create account: `testuser` / `password123`
3. Should auto-login and redirect to dashboard

### Test Document Upload

1. Go to `/dashboard/upload`
2. Upload an image (PNG/JPG)
3. Name it `test_document`
4. Should show upload progress → processing → success

### Test Document Management

1. Go to `/dashboard/documents`
2. Should see uploaded document
3. Click "View Details" to see results
4. Should show extracted text and summary

## 🐛 Troubleshooting

### Backend Not Running

```bash
❌ Health check failed: fetch failed
```

**Solution**: Start backend services (auth + text extraction)

### CORS Errors

```bash
❌ Access to fetch blocked by CORS policy
```

**Solution**: Backend services should allow frontend origin (usually automatic)

### Token Expired

```bash
❌ 401 Unauthorized
```

**Solution**: Automatic logout and redirect to login page

### Upload Fails

```bash
❌ Upload failed with status: 400
```

**Solution**: Check file type (PNG/JPG only) and document name uniqueness

## 🔄 Next Steps

The integration is now complete and functional! You can:

1. **Add more file types** - Extend backend to support PDFs
2. **Add document deletion** - Implement DELETE endpoints
3. **Add user settings** - Profile editing capabilities
4. **Add sharing** - Document sharing between users
5. **Add analytics** - Usage statistics and insights

## 📚 Code Structure

```
frontend/
├── lib/
│   └── api.ts                 # API service layer
├── contexts/
│   └── auth-context.tsx       # Authentication state
├── components/
│   ├── auth/
│   │   ├── login-form.tsx     # Login with API
│   │   └── register-form.tsx  # Registration with API
│   ├── documents/
│   │   ├── document-list.tsx  # Document listing with API
│   │   └── document-detail.tsx# Document viewer
│   └── upload/
│       └── document-upload.tsx# Upload with API
└── app/
    ├── layout.tsx            # AuthProvider wrapper
    ├── page.tsx              # Landing/login page
    ├── register/page.tsx     # Registration page
    └── dashboard/            # Protected dashboard
```

The frontend is now fully connected to your Document Intelligence backend! 🎉
