import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import AppLayout from './layouts/AppLayout';
import SetupPage from './pages/SetupPage';
import ChatPage from './pages/ChatPage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/setup" replace />} />
          <Route path="setup" element={<SetupPage />} />
          <Route path="chat" element={<ChatPage />} />
        </Route>
      </Routes>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#0f0f0f',
            color: '#d4f701',
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 11,
            border: '1px solid #2a2a2a',
            borderRadius: 0,
          },
          success: {
            iconTheme: { primary: '#d4f701', secondary: '#000' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#000' },
            style: {
              background: '#0f0f0f',
              color: '#fca5a5',
              border: '1px solid #3f1111',
            },
          },
        }}
      />
    </BrowserRouter>
  );
}
