import React, { useState } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox,
  Grid,
} from '@mui/material';
import Layout from '../components/Layout';
import { dataAPI } from '../services/api';

function DataGeneration() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    num_patients: 100,
    seed: 42,
    include_vitals: true,
    include_treatments: true,
    apply_privacy: false,
    epsilon: 1.0,
    delta: 0.00001,
  });

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value,
    });
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const params = {
        num_patients: parseInt(formData.num_patients),
        seed: parseInt(formData.seed),
        output_directory: '/tmp/medisafe_generated',
        include_vitals: formData.include_vitals,
        include_treatments: formData.include_treatments,
        apply_privacy: formData.apply_privacy,
      };

      if (formData.apply_privacy) {
        params.privacy_config = {
          epsilon: parseFloat(formData.epsilon),
          delta: parseFloat(formData.delta),
        };
      }

      const response = await dataAPI.generateBatch(params);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error_message || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Typography variant="h4" gutterBottom>
        Generate Synthetic Data
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Data Generation Configuration
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Number of Patients"
              name="num_patients"
              type="number"
              value={formData.num_patients}
              onChange={handleChange}
              helperText="Number of synthetic patient records to generate"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Random Seed"
              name="seed"
              type="number"
              value={formData.seed}
              onChange={handleChange}
              helperText="For reproducible results (optional)"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.include_vitals}
                  onChange={handleChange}
                  name="include_vitals"
                />
              }
              label="Include Vital Signs (BP, Heart Rate, etc.)"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.include_treatments}
                  onChange={handleChange}
                  name="include_treatments"
                />
              }
              label="Include Treatment Assignments"
            />
          </Grid>

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.apply_privacy}
                  onChange={handleChange}
                  name="apply_privacy"
                />
              }
              label="Apply Differential Privacy"
            />
          </Grid>

          {formData.apply_privacy && (
            <>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Epsilon (ε)"
                  name="epsilon"
                  type="number"
                  inputProps={{ step: 0.1, min: 0.1, max: 10 }}
                  value={formData.epsilon}
                  onChange={handleChange}
                  helperText="Privacy budget (lower = more private)"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Delta (δ)"
                  name="delta"
                  type="number"
                  inputProps={{ step: 0.00001 }}
                  value={formData.delta}
                  onChange={handleChange}
                  helperText="Privacy parameter (typically 1e-5)"
                />
              </Grid>
            </>
          )}
        </Grid>

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Generate Data'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 3 }}>
            {error}
          </Alert>
        )}

        {result && result.status === 'success' && (
          <Alert severity="success" sx={{ mt: 3 }}>
            <Typography variant="subtitle1">
              Successfully generated {result.data.records_generated} patient records!
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Files generated:
            </Typography>
            <ul>
              {Object.entries(result.data.files).map(([key, path]) => (
                <li key={key}>
                  <Typography variant="body2">
                    {key}: {path}
                  </Typography>
                </li>
              ))}
            </ul>
          </Alert>
        )}
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          About Synthetic Data Generation
        </Typography>
        <Typography variant="body2" paragraph>
          This tool generates realistic but entirely synthetic healthcare data that:
        </Typography>
        <ul>
          <li>
            <Typography variant="body2">
              Contains no real patient information (HIPAA compliant)
            </Typography>
          </li>
          <li>
            <Typography variant="body2">
              Preserves statistical properties of real healthcare data
            </Typography>
          </li>
          <li>
            <Typography variant="body2">
              Can be used for testing, research, and development
            </Typography>
          </li>
          <li>
            <Typography variant="body2">
              Optionally includes differential privacy for extra protection
            </Typography>
          </li>
        </ul>
      </Paper>
    </Layout>
  );
}

export default DataGeneration;
