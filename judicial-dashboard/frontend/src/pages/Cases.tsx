import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  CircularProgress,
  Alert,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
} from '@mui/material';
import { apiService, Case } from '../services/apiService';

const Cases: React.FC = () => {
  const [cases, setCases] = useState<Case[]>([]);
  const [filtered, setFiltered] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('All');
  const [regionFilter, setRegionFilter] = useState<string>('All');

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const response = await apiService.getCases();
      setCases(response.cases);
      setFiltered(response.cases);
    } catch (err) {
      setError('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let result = cases;
    if (typeFilter !== 'All') {
      result = result.filter(c => c.case_type.toLowerCase() === typeFilter.toLowerCase());
    }
    if (regionFilter !== 'All') {
      result = result.filter(c => c.location_region.toLowerCase() === regionFilter.toLowerCase());
    }
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(c =>
        c.case_id.toLowerCase().includes(q) ||
        c.court_id.toLowerCase().includes(q) ||
        c.case_type.toLowerCase().includes(q) ||
        c.location_region.toLowerCase().includes(q)
      );
    }
    setFiltered(result);
  }, [cases, query, typeFilter, regionFilter]);

  const getCaseTypeColor = (caseType: string) => {
    switch (caseType.toLowerCase()) {
      case 'civil':
        return 'primary';
      case 'criminal':
        return 'error';
      case 'land':
        return 'success';
      default:
        return 'default';
    }
  };

  const getOutcomeColor = (outcome: string) => {
    switch (outcome.toLowerCase()) {
      case 'settled':
        return 'success';
      case 'convicted':
        return 'error';
      case 'dismissed':
        return 'warning';
      default:
        return 'default';
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

  return (
    <Box sx={{ px: 0 }}>
      <Typography variant="h4" gutterBottom>
        Cases Management
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        <TextField
          label="Search"
          placeholder="Search by Case ID, Court, Type, Region"
          size="small"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel id="type-filter-label">Case Type</InputLabel>
          <Select
            labelId="type-filter-label"
            value={typeFilter}
            label="Case Type"
            onChange={(e: SelectChangeEvent) => setTypeFilter(e.target.value as string)}
          >
            <MenuItem value="All">All</MenuItem>
            <MenuItem value="Civil">Civil</MenuItem>
            <MenuItem value="Criminal">Criminal</MenuItem>
            <MenuItem value="Land">Land</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel id="region-filter-label">Region</InputLabel>
          <Select
            labelId="region-filter-label"
            value={regionFilter}
            label="Region"
            onChange={(e: SelectChangeEvent) => setRegionFilter(e.target.value as string)}
          >
            <MenuItem value="All">All</MenuItem>
            <MenuItem value="Central">Central</MenuItem>
            <MenuItem value="Northern">Northern</MenuItem>
            <MenuItem value="Eastern">Eastern</MenuItem>
            <MenuItem value="Western">Western</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Case ID</TableCell>
                <TableCell>Court</TableCell>
                <TableCell>Region</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Filing Date</TableCell>
                <TableCell>Resolution Date</TableCell>
                <TableCell>Duration (Days)</TableCell>
                <TableCell>Hearings</TableCell>
                <TableCell>Adjournments</TableCell>
                <TableCell>Outcome</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((caseItem) => (
                <TableRow key={caseItem.case_id} hover>
                  <TableCell>{caseItem.case_id}</TableCell>
                  <TableCell>{caseItem.court_id}</TableCell>
                  <TableCell>{caseItem.location_region}</TableCell>
                  <TableCell>
                    <Chip
                      label={caseItem.case_type}
                      color={getCaseTypeColor(caseItem.case_type) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{new Date(caseItem.filing_date).toLocaleDateString()}</TableCell>
                  <TableCell>
                    {caseItem.resolution_date 
                      ? new Date(caseItem.resolution_date).toLocaleDateString()
                      : 'Pending'
                    }
                  </TableCell>
                  <TableCell>{caseItem.time_to_resolution_days}</TableCell>
                  <TableCell>{caseItem.num_hearings}</TableCell>
                  <TableCell>{caseItem.num_adjournments}</TableCell>
                  <TableCell>
                    <Chip
                      label={caseItem.outcome_category}
                      color={getOutcomeColor(caseItem.outcome_category) as any}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default Cases;
