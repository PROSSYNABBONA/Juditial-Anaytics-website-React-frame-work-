import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  Schedule,
  Gavel,
  Assessment,
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { apiService } from '../services/apiService';

interface DashboardData {
  total_cases: number;
  avg_resolution_time: number;
  cases_by_type: Record<string, number>;
  cases_by_region: Record<string, number>;
  avg_hearings: number;
  avg_adjournments: number;
}

interface RecentCaseRow {
  case_id: string;
  location_region: string;
  case_type: string;
  filing_date: string;
  resolution_date: string;
  time_to_resolution_days?: number;
  outcome_category?: string;
}

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentCases, setRecentCases] = useState<RecentCaseRow[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Refresh when data changes elsewhere (e.g., after uploads/training in Predictions)
  useEffect(() => {
    const handleDataUpdated = () => {
      fetchDashboardData();
    };
    (window as any).addEventListener('data-updated', handleDataUpdated);
    return () => (window as any).removeEventListener('data-updated', handleDataUpdated);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [summaryRes, casesRes] = await Promise.all([
        apiService.getAnalyticsSummary(),
        apiService.getCases().catch(() => ({ cases: [], total: 0 })),
      ]);
      setData(summaryRes.summary);
      const rows: RecentCaseRow[] = (casesRes.cases || []).map((c: any) => ({
        case_id: c.case_id,
        location_region: c.location_region,
        case_type: c.case_type,
        filing_date: c.filing_date,
        resolution_date: c.resolution_date,
        time_to_resolution_days: c.time_to_resolution_days,
        outcome_category: c.outcome_category,
      }));
      // Sort by filing_date desc and take recent 10
      rows.sort((a, b) => (b.filing_date || '').localeCompare(a.filing_date || ''));
      setRecentCases(rows.slice(0, 10));
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

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

  if (!data) {
    return <Alert severity="warning">No data available</Alert>;
  }

  const caseTypeData = Object.entries(data.cases_by_type).map(([type, count]) => ({
    name: type,
    value: count,
  }));

  const regionData = Object.entries(data.cases_by_region).map(([region, count]) => ({
    name: region,
    value: count,
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  // Removed disposal rate and backlog per request

  // recentCases now comes from API

  const kpiTrend = [
    { month: 'Jan', value: 45 },
    { month: 'Feb', value: 52 },
    { month: 'Mar', value: 48 },
    { month: 'Apr', value: 61 },
    { month: 'May', value: 55 },
    { month: 'Jun', value: 67 },
  ];

  return (
    <Box sx={{ px: 0 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
        <Typography variant="h4" gutterBottom align="center" sx={{ width: '100%' }}>
          Judicial Analytics Dashboard
        </Typography>
      </Box>
      
      <Grid container spacing={2} alignItems="stretch">
        {/* Charts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, minHeight: 340, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Cases by Type
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={caseTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {caseTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, minHeight: 340, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Cases by Region
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={regionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Trend Mini Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, minHeight: 240, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Case Inflow Trend
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={kpiTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#1976d2" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Cases */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Cases
            </Typography>
            <TableContainer sx={{ width: '100%', overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Case ID</TableCell>
                    <TableCell>Region</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Filing Date</TableCell>
                    <TableCell>Resolution Date</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Outcome</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentCases.map((rc) => (
                    <TableRow key={rc.case_id}>
                      <TableCell>{rc.case_id}</TableCell>
                      <TableCell>{rc.location_region}</TableCell>
                      <TableCell>
                        <Chip label={rc.case_type} size="small" color={rc.case_type === 'Criminal' ? 'error' : 'primary'} />
                      </TableCell>
                      <TableCell>{rc.filing_date || ''}</TableCell>
                      <TableCell>{rc.resolution_date || ''}</TableCell>
                      <TableCell>{rc.time_to_resolution_days != null ? `${rc.time_to_resolution_days} days` : ''}</TableCell>
                      <TableCell>
                        <Chip label={rc.outcome_category || ''} size="small" color={rc.outcome_category === 'Convicted' ? 'error' : 'success'} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
