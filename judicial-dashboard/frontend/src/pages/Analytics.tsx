import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { apiService } from '../services/apiService';

const Analytics: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  // Refresh when other pages update data (e.g., after training/uploads)
  useEffect(() => {
    const handleDataUpdated = () => fetchAnalyticsData();
    (window as any).addEventListener('data-updated', handleDataUpdated);
    return () => (window as any).removeEventListener('data-updated', handleDataUpdated);
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAnalyticsSummary();
      setData(response.summary);
    } catch (err) {
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const [timeSeriesData, setTimeSeriesData] = useState<Array<{ month: string; cases: number; resolution: number }>>([]);
  const [resolutionTimeData, setResolutionTimeData] = useState<Array<{ category: string; count: number }>>([]);
  const [courtPerformance, setCourtPerformance] = useState<Array<{ court: string; rate: number }>>([]);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [region, setRegion] = useState<string>('');
  const [caseType, setCaseType] = useState<string>('');

  const loadAll = async () => {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (region) params.region = region; // comma separated if multiple later
    if (caseType) params.case_type = caseType;
    try {
      const [ts, rd, cp, sum] = await Promise.all([
        apiService.getTimeSeries(params),
        apiService.getResolutionDistribution(params),
        apiService.getCourtPerformance(params),
        apiService.getAnalyticsSummary(),
      ]);
      setTimeSeriesData(ts.series || []);
      setResolutionTimeData(rd.distribution || []);
      setCourtPerformance(cp.performance || []);
      setData(sum.summary);
    } catch (e) {}
  };

  useEffect(() => {
    loadAll();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box sx={{ px: 0 }}>
      <Typography variant="h4" gutterBottom>
        Analytics & Insights
      </Typography>
      
      <Grid container spacing={3}>
        {/* Export metrics to report */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="contained" onClick={async () => {
              try {
                await apiService.exportMetricsToReport();
                alert('Report updated with latest metrics.');
              } catch (_) {
                alert('Failed to update report.');
              }
            }}>Export metrics to report</Button>
          </Paper>
        </Grid>
        {/* Filters */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Typography variant="body2">Start</Typography>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Typography variant="body2">End</Typography>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Typography variant="body2">Region</Typography>
              <input placeholder="e.g., Central" value={region} onChange={(e) => setRegion(e.target.value)} />
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Typography variant="body2">Case Type</Typography>
              <input placeholder="e.g., Civil" value={caseType} onChange={(e) => setCaseType(e.target.value)} />
            </Box>
            <Button variant="outlined" onClick={loadAll}>Apply</Button>
          </Paper>
        </Grid>
        {/* Case Flow Over Time */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Case Flow Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="cases" stroke="#8884d8" strokeWidth={2} name="New Cases" />
                <Line type="monotone" dataKey="resolution" stroke="#82ca9d" strokeWidth={2} name="Resolved Cases" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Resolution Time Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Resolution Time Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resolutionTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Performance Metrics
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body1" gutterBottom>
                <strong>Average Resolution Time:</strong> {data?.avg_resolution_time} days
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Average Hearings per Case:</strong> {data?.avg_hearings}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Average Adjournments per Case:</strong> {data?.avg_adjournments}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Total Cases:</strong> {data?.total_cases}
              </Typography>
              {(data?.disposal_rate !== undefined || (data?.resolved_cases !== undefined && data?.total_cases)) && (
                <Typography variant="body1" gutterBottom>
                  <strong>Disposal Rate:</strong> {(
                    data?.disposal_rate !== undefined
                      ? data.disposal_rate * 100
                      : (data?.resolved_cases / Math.max(1, data?.total_cases)) * 100
                  ).toFixed(1)}%
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Case Type Analysis */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Case Type Analysis
            </Typography>
            <Box sx={{ mt: 2 }}>
              {data?.cases_by_type && Object.entries(data.cases_by_type).map(([type, count]) => (
                <Box key={type} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">{type}</Typography>
                  <Typography variant="body2" color="primary">{`${count} cases`}</Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Adjournment Reasons */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Adjournment Reasons (Sample)
            </Typography>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={courtPerformance.map(cp => ({ reason: cp.court, count: Math.round(cp.rate * 100) }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="reason" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Court Performance (heatmap-like bars) */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Court Performance (Resolution Rate)
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 3fr 1fr', gap: 1 }}>
              {courtPerformance.map((cp) => (
                <React.Fragment key={cp.court}>
                  <Typography variant="body2">{cp.court}</Typography>
                  <Box sx={{ background: '#eee', borderRadius: 1 }}>
                    <Box sx={{ width: `${Math.round(cp.rate * 100)}%`, background: '#1976d2', height: 12, borderRadius: 1 }} />
                  </Box>
                  <Typography variant="body2" color="primary">{Math.round(cp.rate * 100)}%</Typography>
                </React.Fragment>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;
