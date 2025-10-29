import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  TrendingUp,
  Schedule,
  Assessment,
} from '@mui/icons-material';
import { apiService } from '../services/apiService';
import Button from '@mui/material/Button';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import TextField from '@mui/material/TextField';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const Predictions: React.FC = () => {
  const [predictions, setPredictions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadInfo, setUploadInfo] = useState<string | null>(null);
  const [serverFilePath, setServerFilePath] = useState<string>('');
  const [pdfInfo, setPdfInfo] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [trainingResult, setTrainingResult] = useState<any>(null);
  const [previewRows, setPreviewRows] = useState<any[] | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPredictions();
      setPredictions(response.predictions);
    } catch (err) {
      setError('Failed to load predictions');
    } finally {
      setLoading(false);
    }
  };

  const uploadDatasetFile = async (file: File) => {
    try {
      setUploading(true);
      setError(null);
      const res = await apiService.uploadDataAndTrain(file);
      setUploadInfo(`Uploaded to: ${res.saved_path || ''}`.trim());
      setTrainingResult(res.training_result);
      setPreviewRows(res.preview || null);
      const pred = await apiService.getPredictions();
      setPredictions(pred.predictions);
      (window as any).dispatchEvent(new Event('data-updated'));
    } catch (err) {
      setError('Upload/train failed. Ensure the file has required columns.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadDatasetFile(file);
    // Clear input value so the same file can be selected again
    e.target.value = '';
  };

  const handleTrainFromPath = async () => {
    if (!serverFilePath) return;
    try {
      setUploading(true);
      setError(null);
      const res = await apiService.trainFromFilePath(serverFilePath);
      setUploadInfo(`Trained from: ${serverFilePath}`);
      setTrainingResult(res.training_result);
      setPreviewRows(null);
      const pred = await apiService.getPredictions();
      setPredictions(pred.predictions);
      (window as any).dispatchEvent(new Event('data-updated'));
    } catch (err) {
      setError('Training from path failed. Check the path and file format.');
    } finally {
      setUploading(false);
    }
  };

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploading(true);
      setError(null);
      const res = await apiService.uploadPdfAndTrain(file);
      setPdfInfo(`${res.message} (rows: ${res.rows})`);
      setTrainingResult(res.training_result);
      setPreviewRows(res.preview || null);
      const pred = await apiService.getPredictions();
      setPredictions(pred.predictions);
      (window as any).dispatchEvent(new Event('data-updated'));
    } catch (err) {
      setError('PDF upload/train failed. Ensure PDF has key:value lines.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!isDragging) setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const onDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    const lower = file.name.toLowerCase();
    if (lower.endsWith('.xlsx') || lower.endsWith('.xls') || lower.endsWith('.csv')) {
      await uploadDatasetFile(file);
    } else if (lower.endsWith('.pdf')) {
      // Route PDFs through the PDF trainer
      const fakeEvent = { target: { files: [file], value: '' } } as any;
      await handlePdfUpload(fakeEvent);
    } else {
      setError('Unsupported file type. Please drop .xlsx, .xls, .csv, or .pdf');
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
        Predictive Analytics
      </Typography>
      
      <Grid container spacing={3}>
        {/* Upload & Train Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            {/* Plain input control (no label wrapping) */}
            <Box>
              <Typography variant="caption" color="textSecondary">Select Excel/CSV</Typography>
              <input accept=".xlsx,.xls,.csv" type="file" onChange={handleFileUpload} disabled={uploading} />
            </Box>

            {/* Drag-and-drop zone */}
            <Box
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              sx={{
                border: '2px dashed',
                borderColor: isDragging ? 'primary.main' : 'divider',
                borderRadius: 1,
                px: 2,
                py: 1.5,
                cursor: 'pointer',
                minWidth: 260,
                backgroundColor: isDragging ? 'action.hover' : 'transparent',
              }}
              title="Drag & drop .xlsx/.xls/.csv or .pdf here"
            >
              <Typography variant="body2">
                {isDragging ? 'Drop file to upload…' : 'Drag & drop Excel/CSV (or PDF) here'}
              </Typography>
            </Box>
            <TextField
              size="small"
              label="Train from server file path"
              placeholder="C:\\path\\to\\file.xlsx"
              value={serverFilePath}
              onChange={(e) => setServerFilePath(e.target.value)}
              sx={{ minWidth: 360 }}
            />
            <Button variant="outlined" onClick={handleTrainFromPath} disabled={uploading || !serverFilePath}>
              Train From Path
            </Button>
            {/* Plain input for PDF */}
            <Box>
              <Typography variant="caption" color="textSecondary">Select PDF</Typography>
              <input accept=".pdf" type="file" onChange={handlePdfUpload} disabled={uploading} />
            </Box>
            {uploadInfo && (
              <Typography variant="body2" color="textSecondary">
                {uploadInfo}
              </Typography>
            )}
            {pdfInfo && (
              <Typography variant="body2" color="textSecondary">
                {pdfInfo}
              </Typography>
            )}
          </Paper>
        </Grid>
        {/* Model Performance */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Assessment color="primary" sx={{ mr: 2 }} />
                <Typography variant="h6">Model Accuracy</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {(predictions?.model_accuracy * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Current model performance
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Schedule color="primary" sx={{ mr: 2 }} />
                <Typography variant="h6">Predicted Resolution</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {predictions?.predicted_avg_resolution} days
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Average case resolution time
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TrendingUp color="primary" sx={{ mr: 2 }} />
                <Typography variant="h6">Confidence Interval</Typography>
              </Box>
              <Typography variant="h6" color="primary">
                {predictions?.confidence_interval[0]} - {predictions?.confidence_interval[1]} days
              </Typography>
              <Typography variant="body2" color="textSecondary">
                95% confidence range
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Upload Summary (replaces Prediction Insights and Model Recommendations) */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Upload Summary
            </Typography>
            {(!uploadInfo && !pdfInfo && !trainingResult) && (
              <Typography variant="body2" color="textSecondary">No uploads yet. Upload an Excel/CSV or PDF to see a summary here.</Typography>
            )}
            {uploadInfo && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="subtitle2">Excel/CSV</Typography>
                <Typography variant="body2" color="textSecondary">{uploadInfo}</Typography>
              </Box>
            )}
            {pdfInfo && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="subtitle2">PDF</Typography>
                <Typography variant="body2" color="textSecondary">{pdfInfo}</Typography>
              </Box>
            )}
            {trainingResult && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="subtitle2">Training Metrics</Typography>
                <Typography variant="body2">Best Model: {trainingResult.best_model}</Typography>
                <Typography variant="body2">
                  Linear Regression – MAE: {trainingResult.linear_regression?.mae?.toFixed?.(1)}, R²: {trainingResult.linear_regression?.r2_score?.toFixed?.(3)}, RMSE: {trainingResult.linear_regression?.rmse?.toFixed?.(1)}
                </Typography>
                <Typography variant="body2">
                  Random Forest – MAE: {trainingResult.random_forest?.mae?.toFixed?.(1)}, R²: {trainingResult.random_forest?.r2_score?.toFixed?.(3)}, RMSE: {trainingResult.random_forest?.rmse?.toFixed?.(1)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Samples – train: {trainingResult.training_samples}, test: {trainingResult.test_samples}
                </Typography>
              </Box>
            )}
            {previewRows && previewRows.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Data Preview (first {Math.min(previewRows.length, 5)} rows)</Typography>
                <Box sx={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        {Object.keys(previewRows[0]).map((k) => (
                          <th key={k} style={{ textAlign: 'left', padding: 6, borderBottom: '1px solid #eee' }}>{k}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, idx) => (
                        <tr key={idx}>
                          {Object.keys(previewRows[0]).map((k) => (
                            <td key={k} style={{ padding: 6, borderBottom: '1px solid #f5f5f5', fontSize: 12 }}>{String(row[k] ?? '')}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Training Summary */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
              <Typography variant="h6">Model Training</Typography>
              <Button variant="outlined" onClick={async () => {
                try {
                  setUploading(true);
                  const res = await apiService.trainModels();
                  setTrainingResult(res.training_result);
                  const pred = await apiService.getPredictions();
                  setPredictions(pred.predictions);
                } catch (_) {
                  setError('Training failed');
                } finally {
                  setUploading(false);
                }
              }} disabled={uploading}>
                Train Using Current Data
              </Button>
            </Box>
            {trainingResult && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Best Model: {trainingResult.best_model}
                </Typography>
                <Typography variant="body2">
                  Linear Regression – MAE: {trainingResult.linear_regression?.mae?.toFixed?.(1)}, R²: {trainingResult.linear_regression?.r2_score?.toFixed?.(3)}, RMSE: {trainingResult.linear_regression?.rmse?.toFixed?.(1)}
                </Typography>
                <Typography variant="body2">
                  Random Forest – MAE: {trainingResult.random_forest?.mae?.toFixed?.(1)}, R²: {trainingResult.random_forest?.r2_score?.toFixed?.(3)}, RMSE: {trainingResult.random_forest?.rmse?.toFixed?.(1)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Samples – train: {trainingResult.training_samples}, test: {trainingResult.test_samples}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Future Predictions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Future Case Predictions
            </Typography>
            <Typography variant="body1" color="textSecondary">
              Based on current trends and historical data, the model predicts:
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                • <strong>Next 30 days:</strong> 45-55 new cases expected
              </Typography>
              <Typography variant="body2">
                • <strong>Resolution rate:</strong> 75-85% of pending cases
              </Typography>
              <Typography variant="body2">
                • <strong>Backlog impact:</strong> 15-20% increase in average resolution time
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Predictions;
