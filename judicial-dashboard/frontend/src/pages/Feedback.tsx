import React, { useState } from 'react';
import { Box, Paper, Typography, TextField, Button, Rating, Alert } from '@mui/material';
import { apiService } from '../services/apiService';

const Feedback: React.FC = () => {
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [rating, setRating] = useState<number | null>(4);
  const [comments, setComments] = useState('');
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      setSuccess(null);
      await apiService.submitFeedback({ name, role, rating: rating || 0, comments });
      setSuccess('Thank you for your feedback!');
      setName(''); setRole(''); setRating(4); setComments('');
    } catch (e) {
      setError('Failed to submit feedback');
    }
  };

  return (
    <Box sx={{ px: 0 }}>
      <Typography variant="h4" gutterBottom>Usability Test & Feedback</Typography>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>Checklist (for facilitator)</Typography>
        <Typography variant="body2" color="textSecondary">
          - Can the user find case KPIs quickly?<br/>
          - Can the user filter analytics by date/region/type?<br/>
          - Can the user upload a dataset and see updates?<br/>
          - Are metrics understandable (avg time, disposal rate)?<br/>
          - How confident is the user in predictions?<br/>
        </Typography>
      </Paper>
      <Paper sx={{ p: 3 }}>
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={handleSubmit}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} />
            <TextField label="Role (Judge, Registrar, ...)" value={role} onChange={(e) => setRole(e.target.value)} />
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
            <Typography variant="body2">Overall rating:</Typography>
            <Rating value={rating} onChange={(_, v) => setRating(v)} />
          </Box>
          <TextField label="Comments" value={comments} onChange={(e) => setComments(e.target.value)} fullWidth multiline minRows={4} sx={{ mt: 2 }} />
          <Button type="submit" variant="contained" sx={{ mt: 2 }}>Submit Feedback</Button>
        </form>
      </Paper>
    </Box>
  );
};

export default Feedback;


