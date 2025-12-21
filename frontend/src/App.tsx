import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import CallDetails from './pages/CallDetails';
import BotSettings from './pages/BotSettings';
import KnowledgeBase from './pages/KnowledgeBase';
import TestBot from './pages/TestBot';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/calls/:callId"
            element={
              <ProtectedRoute>
                <CallDetails />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/bot"
            element={
              <ProtectedRoute>
                <BotSettings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/knowledge"
            element={
              <ProtectedRoute>
                <KnowledgeBase />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/test"
            element={
              <ProtectedRoute>
                <TestBot />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
