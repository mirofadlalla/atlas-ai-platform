# Atlas AI Platform - Frontend

Professional React frontend for the Atlas AI Platform with advanced RAG pipeline, document reranking, cost analytics, and multi-tenant support.

## 🎯 Features

### User Interface
- **Authentication System** - Secure JWT-based login with invitation-only registration
- **Query Interface** - Real-time document retrieval with reranking score visualization
- **Data Ingestion** - File upload with support for recursive directory ingestion
- **Evaluation Dashboard** - Run and monitor RAG pipeline evaluations
- **Cost Analytics** - Track usage, costs, and performance metrics
- **Admin Panel** - Manage users, invitations, and approvals

### Technical Capabilities
- ✅ Streaming responses with auto-scroll
- ✅ Reranking score visualization (semantic, lexical, combined)
- ✅ Real-time error handling and user feedback
- ✅ Responsive mobile-first design
- ✅ Role-based UI rendering (admin/user tiers)
- ✅ Token-based authentication persistence

## 📋 Prerequisites

- **Node.js** 16+ and npm 8+
- **Atlas AI Backend** running on `http://localhost:8000`
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Update `.env` with your configuration:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENABLE_RERANKING=true
REACT_APP_ENABLE_EVALUATION=true
REACT_APP_ENABLE_ANALYTICS=true
```

### 3. Start Development Server

```bash
npm start
```

The application will open at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html           # HTML entry point
├── src/
│   ├── index.js            # React entry point
│   ├── index.css           # Global styles
│   ├── App.jsx             # Main app component with routing
│   ├── services/
│   │   └── apiService.js   # Unified API client for all endpoints
│   ├── components/
│   │   ├── Navigation.jsx  # Header with nav links and logout
│   │   ├── Navigation.css
│   │   ├── ProtectedRoute.jsx  # Route protection wrapper
│   │   └── ...
│   └── pages/
│       ├── LoginPage.jsx   # User authentication
│       ├── LoginPage.css
│       ├── RegisterPage.jsx # Invitation-based registration
│       ├── DashboardPage.jsx # Navigation hub
│       ├── DashboardPage.css
│       ├── QueryPage.jsx   # Document search and retrieval
│       ├── QueryPage.css
│       ├── IngestPage.jsx  # File upload interface
│       ├── IngestPage.css
│       ├── AdminPanel.jsx  # User management
│       ├── AdminPanel.css
│       ├── EvaluationPage.jsx # Pipeline evaluation
│       ├── EvaluationPage.css
│       ├── CostAnalyticsPage.jsx # Usage analytics
│       ├── CostAnalyticsPage.css
│       └── ...
├── package.json            # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔐 Authentication Flow

### 1. **Invitation-Based Registration**
   - Admin sends invitation token to email
   - User enters token on registration page
   - User sets password and creates account
   - Admin approves user before access

### 2. **Login Process**
   - User enters email and password
   - System validates credentials and returns JWT token
   - Token stored in localStorage for session persistence
   - Requests include token in `Authorization` header

### 3. **Access Control**
   - Unauthenticated users redirected to login
   - Routes protected by `ProtectedRoute` wrapper
   - Admin features only visible to admin-role users
   - Session expires after 30 minutes of inactivity

## 📱 Page Documentation

### LoginPage
**Purpose**: User authentication

**Features**:
- Email/password form validation
- Persistent session using JWT
- Error handling with user feedback
- Link to invitation-based registration

**Example**:
```jsx
// Automatic token storage
localStorage.setItem('token', response.token);
localStorage.setItem('user', JSON.stringify(response.user));
```

### RegisterPage
**Purpose**: Invitation-only user registration

**Features**:
- Token validation before registration
- Secure password creation
- Auto-populated email from token
- Prevents duplicate registrations

**Example**:
```
1. User enters invitation token
2. System validates and retrieves email
3. User sets password
4. Account created, user awaits admin approval
```

### DashboardPage
**Purpose**: Main application hub

**Features**:
- 6 navigation cards (Query, Ingest, Evaluate, Analytics, Admin)
- User profile with stats (queries, documents, costs)
- Role-based admin panel access
- Quick action buttons

### QueryPage
**Purpose**: Document retrieval and Q&A

**Features**:
- Tab interface (Answer vs. Documents)
- Streaming response with real-time display
- Document retrieval with metadata
- **Reranking Score Visualization**:
  - Original Score: Initial semantic similarity
  - Rerank Score: Cross-encoder refinement
  - Combined Score: Weighted hybrid result
- Cost tracking per query

**Example Query**:
```
Input: "How does the reranker improve retrieval?"

Response Tabs:
1. Answer Tab: "The reranker combines semantic..." [streaming]
2. Documents Tab:
   - Doc 1: "Reranking Strategies..." 
     Original: 92.5% | Rerank: 95.2% | Combined: 93.8%
   - Doc 2: "Hybrid Approach..."
     Original: 87.3% | Rerank: 89.1% | Combined: 88.2%
```

### IngestPage
**Purpose**: Data ingestion and indexing

**Features**:
- File path input (local file system)
- Recursive directory support
- File source metadata (document source)
- Author information tracking
- Progress feedback

**Example**:
```
Path: /data/documents/
Source: Research Papers
Author: John Doe
Recursive: ✓ (includes subdirectories)
```

### AdminPanel
**Purpose**: User and invitation management

**Features**:
- Two tabs: Send Invitations | Approve Users
- **Invitations Tab**:
  - Send invites to email addresses
  - View pending invitations
  - Resend expired invitations
  - Track invitation status
- **Approvals Tab**:
  - List pending user approvals
  - View user details (email, created_at)
  - Approve or reject registration requests

### EvaluationPage
**Purpose**: RAG pipeline evaluation

**Features**:
- Upload evaluation dataset (JSON format)
- Configure evaluation runs
- Metrics tracked:
  - Precision@K - Relevant documents in top K results
  - Recall@K - Coverage of relevant documents
  - F1 Score - Harmonic mean metric
  - MRR - Mean Reciprocal Rank
  - Jaccard Stability - Consistency measure
  - Token F1 - Keyword overlap

**Dataset Format**:
```json
[
  {
    "query": "What is the reranking strategy?",
    "ground_truth": ["doc1.pdf", "doc3.pdf"],
    "expected_answer": "Hybrid approach combining..."
  }
]
```

### CostAnalyticsPage
**Purpose**: Usage monitoring and cost analysis

**Features**:
- Cost summary (total, average, per-query)
- Cost breakdown by model
- Usage metrics (latency, cache hit rate)
- Token tracking (input/output)
- Optimization recommendations
- Integration with MLflow dashboard

## 🔌 API Integration

### API Service Structure

The `apiService.js` provides unified methods for all backend endpoints:

```javascript
// Authentication
apiService.login(email, password)
apiService.register(email, password, tenantName)
apiService.registerViaInvitation(token, password)
apiService.getProfile()

// Queries
apiService.askQuery(query)
apiService.retrieveDocuments(query, top_k)

// Ingestion
apiService.uploadFile(filePath, source, author, recursive)

// Admin
apiService.sendInvitation(email)
apiService.validateInvitation(token)
apiService.getPendingApprovals()
apiService.approveUser(userId)

// Analytics
apiService.getCostAnalytics()
apiService.getRuns()
```

### Error Handling

All API calls include try-catch with user-friendly error messages:

```javascript
try {
  const data = await apiService.askQuery(query);
  setAnswer(data.answer);
} catch (error) {
  setError(error.message); // "Invalid query" or "Rate limit exceeded"
}
```

### Authentication Headers

All requests automatically include:

```javascript
headers: {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`,
  'X-User-ID': userId,
  'X-Role': userRole,
  'X-Tenant-ID': tenantId
}
```

## 🎨 Styling System

### Color Scheme
- **Primary**: #667eea (purple-blue)
- **Secondary**: #764ba2 (dark purple)
- **Accent**: #f5576c (coral)
- **Success**: #28a745 (green)
- **Warning**: #ffc107 (amber)
- **Error**: #dc3545 (red)

### Responsive Breakpoints
- **Desktop**: 1024px+
- **Tablet**: 768px - 1023px
- **Mobile**: 480px - 767px
- **Small**: < 480px

### Component Patterns
Each page includes:
- Gradient background header
- White content cards with shadows
- Smooth transitions and hover effects
- Mobile-first responsive design
- Accessible form controls

## 🧪 Testing

### Manual Testing Checklist

```javascript
// Test authentication
1. ✓ Can login with valid credentials
2. ✓ Cannot login with invalid password
3. ✓ Can register via valid invitation
4. ✓ Invitations expire correctly

// Test querying
5. ✓ Query returns streamed response
6. ✓ Documents display with reranking scores
7. ✓ Rate limiting blocks excessive queries
8. ✓ Cost is tracked per query

// Test admin functions
9. ✓ Admin can send invitations
10. ✓ Admin can approve/reject users
11. ✓ Non-admin cannot access admin panel

// Test ingestion
12. ✓ Can upload files
13. ✓ Supports recursive directories
14. ✓ Shows progress and completion

// Test analytics
15. ✓ Costs display correctly
16. ✓ Usage metrics update in real-time
17. ✓ Evaluations complete successfully
```

## 📊 Performance Optimization

### Implemented
- ✅ Code splitting with React.lazy
- ✅ Streaming response handling
- ✅ Auto-scrolling for long content
- ✅ Debounced search inputs
- ✅ Cached authentication state
- ✅ Optimized re-renders with React.memo

### Metrics
- **Page Load**: <2s (local network)
- **Query Response**: Streaming in <500ms first byte
- **Memory**: <50MB for typical session

## 🔧 Development

### Available Scripts

```bash
npm start      # Start dev server (port 3000)
npm build      # Build for production
npm test       # Run test suite
npm eject      # Expose create-react-app config (irreversible)
```

### Browser DevTools

- ✅ React DevTools browser extension recommended
- ✅ Network tab for API debugging
- ✅ Application storage shows JWT tokens
- ✅ Console shows API response bodies

### Common Issues

**Issue**: "Cannot find Bearer token"
- **Solution**: Ensure backend is running and login was successful

**Issue**: "Query page shows no documents"
- **Solution**: Check backend reranker is initialized (see backend README)

**Issue**: Admin panel shows no users
- **Solution**: Ensure you're logged in as admin role user

## 📚 Additional Resources

- **Backend Documentation**: See `../IMPLEMENTATION_GUIDE.md`
- **Architecture Diagram**: See `../digrams/archDigram.simp`
- **API Specification**: Backend FastAPI `/docs` endpoint
- **MLflow Tracking**: Visit `http://localhost:5000` for experiment data

## 🤝 Contributing

When adding new features:

1. Create component in appropriate folder
2. Follow existing styling patterns
3. Add error handling with user feedback
4. Include responsive design
5. Test on mobile devices
6. Update this README

## 📝 License

Part of Atlas AI Platform - Production RAG System

## 🚀 Deployment

### Local Development
```bash
npm start
```

### Production Build
```bash
npm run build
# Serve build/ folder with web server
```

### Docker (Optional)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 📞 Support

For issues or questions:
1. Check this README
2. Review backend IMPLEMENTATION_GUIDE.md
3. Check console for error messages
4. Verify backend API is running
5. Check environment variables in .env

---

**Built with React 18 • Styled for Enterprise • Ready for Production**
