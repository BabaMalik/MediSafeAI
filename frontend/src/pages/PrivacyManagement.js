import React, { useState } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { Security, TrendingUp } from '@mui/icons-material';
import Layout from '../components/Layout';
import { dataAPI } from '../services/api';

function PrivacyManagement() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    input_file: '',
    epsilon: 1.0,
    delta: 0.00001,
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleApplyPrivacy = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await dataAPI.applyPrivacy({
        input_file: formData.input_file,
        privacy_config: {
          epsilon: parseFloat(formData.epsilon),
          delta: parseFloat(formData.delta),
        },
        numeric_columns: ['age', 'income'],
        categorical_columns: [],
      });

      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error_message || 'Failed to apply privacy');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Typography variant="h4" gutterBottom>
        Privacy Management
      </Typography>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Security color="primary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Differential Privacy
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Mathematical guarantee that individual records cannot be identified
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp color="secondary" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Privacy Budget
                </Typography>
              </Box>
              <Typography variant="body2" color="textSecondary">
                Track cumulative privacy usage across operations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                HIPAA Compliant
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Full audit logging and privacy tracking
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Apply Differential Privacy
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Input File Path"
              name="input_file"
              value={formData.input_file}
              onChange={handleChange}
              helperText="Path to the CSV file containing patient data"
              placeholder="/tmp/medisafe_generated/patients_*.csv"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Epsilon (ε)"
              name="epsilon"
              type="number"
              inputProps={{ step: 0.1, min: 0.1, max: 10 }}
              value={formData.epsilon}
              onChange={handleChange}
              helperText="Privacy budget (lower = more private, less utility)"
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
              helperText="Typically 1e-5 or smaller"
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleApplyPrivacy}
            disabled={loading || !formData.input_file}
          >
            {loading ? <CircularProgress size={24} /> : 'Apply Privacy'}
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
              Privacy applied successfully!
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Processed {result.data.records_processed} records
            </Typography>
            <Typography variant="body2">
              Output file: {result.data.output_file}
            </Typography>
            <Typography variant="body2">
              Privacy budget used: ε = {result.data.epsilon}, δ = {result.data.delta}
            </Typography>
          </Alert>
        )}
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Understanding Privacy Parameters
        </Typography>

        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Epsilon (ε) - Privacy Budget:
          </Typography>
          <Typography variant="body2" paragraph>
            Lower values provide stronger privacy but may reduce data utility.
            Recommended values: 0.1-1.0 for high privacy, 1.0-10.0 for moderate privacy.
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            Delta (δ) - Privacy Parameter:
          </Typography>
          <Typography variant="body2" paragraph>
            Probability that privacy guarantee fails. Should be much smaller than 1/n
            where n is the dataset size. Typical value: 1e-5
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            Privacy-Utility Tradeoff:
          </Typography>
          <Typography variant="body2">
            More privacy (lower ε) means more noise added to the data, which may
            reduce its usefulness for analysis. Balance privacy needs with data utility
            requirements.
          </Typography>
        </Box>
      </Paper>
    </Layout>
  );
}

export default PrivacyManagement;
