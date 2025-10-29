import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Paper, TextField, Button, Typography, Alert } from '@mui/material';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const form = new URLSearchParams();
      form.append('username', username);
      form.append('password', password);
      form.append('grant_type', 'password');
      const res = await fetch((process.env.REACT_APP_API_URL || 'http://127.0.0.1:8010') + '/api/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('role', data.role);
      navigate('/');
    } catch (err) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      sx={{
        p: 2,
        backgroundImage: `url('/pic.jpg'), url('/pic.png')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <Paper sx={{ p: 3, width: 360, backdropFilter: 'blur(6px)', backgroundColor: 'rgba(255,255,255,0.9)' }}>
        <Typography variant="h6" gutterBottom>Sign in</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={handleSubmit}>
          <TextField label="Username" fullWidth margin="normal" value={username} onChange={(e) => setUsername(e.target.value)} />
          <TextField label="Password" type="password" fullWidth margin="normal" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Button type="submit" variant="contained" fullWidth disabled={loading} sx={{ mt: 2 }}>Login</Button>
        </form>
      </Paper>
    </Box>
  );
};

export default Login;


