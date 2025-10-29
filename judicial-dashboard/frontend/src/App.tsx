import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import Analytics from './pages/Analytics';
import Predictions from './pages/Predictions';
import Login from './pages/Login';
import Feedback from './pages/Feedback';

const isAuthenticated = () => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return false;
    
    // Check if token is expired (basic check)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      if (payload.exp && payload.exp < currentTime) {
        localStorage.removeItem('access_token');
        return false;
      }
    } catch {
      // If token is malformed, remove it
      localStorage.removeItem('access_token');
      return false;
    }
    
    return true;
  } catch {
    return false;
  }
};

const ProtectedLayout: React.FC = () => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Navbar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          mt: 8,
          px: 0,
          pb: 4,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/feedback" element={<Feedback />} />
          </Route>
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
