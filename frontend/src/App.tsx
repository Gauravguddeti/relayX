import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import Calls from './pages/Calls';
import CallDetails from './pages/CallDetails';
import CampaignDetail from './pages/CampaignDetail';
import Contacts from './pages/Contacts';
import AgentSettings from './pages/AgentSettings';
import KnowledgeBase from './pages/KnowledgeBase';
import TestBot from './pages/TestBot';
import CalIntegration from './pages/CalIntegration';

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
            path="/dashboard/calls"
            element={
              <ProtectedRoute>
                <Calls />
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
            path="/campaigns/:campaignId"
            element={
              <ProtectedRoute>
                <CampaignDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/contacts"
            element={
              <ProtectedRoute>
                <Contacts />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/bot"
            element={
              <ProtectedRoute>
                <AgentSettings />
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
          <Route
            path="/dashboard/cal"
            element={
              <ProtectedRoute>
                <CalIntegration />
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
