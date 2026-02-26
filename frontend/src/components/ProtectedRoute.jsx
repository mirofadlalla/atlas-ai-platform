import React from 'react';
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children, isAuthenticated, loading }) {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <p>⏳ Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
