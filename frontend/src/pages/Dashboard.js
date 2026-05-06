import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
} from '@mui/material';
import {
  People,
  Security,
  DataUsage,
  Assessment,
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { utilsAPI } from '../services/api';

function Dashboard() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    loadHealthStatus();
  }, []);

  const loadHealthStatus = async () => {
    try {
      const response = await utilsAPI.healthCheck();
      setHealth(response.data);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  const stats = [
    {
      title: 'Generate Data',
      icon: <People fontSize="large" />,
      description: 'Create synthetic patient, vitals, and treatment data',
      color: '#1976d2',
      link: '/generate',
    },
    {
      title: 'Privacy Management',
      icon: <Security fontSize="large" />,
      description: 'Apply differential privacy and track budget usage',
      color: '#dc004e',
      link: '/privacy',
    },
    {
      title: 'Data Analysis',
      icon: <Assessment fontSize="large" />,
      description: 'Analyze generated data with privacy-preserving statistics',
      color: '#388e3c',
      link: '/generate',
    },
    {
      title: 'System Status',
      icon: <DataUsage fontSize="large" />,
      description: health?.status === 'healthy' ? 'All systems operational' : 'System degraded',
      color: health?.status === 'healthy' ? '#388e3c' : '#f57c00',
    },
  ];

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          HIPAA-Compliant Synthetic Healthcare Data Generator
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                '&:hover': {
                  boxShadow: 6,
                  cursor: stat.link ? 'pointer' : 'default',
                },
              }}
              onClick={() => stat.link && window.location.href = stat.link}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mb: 2,
                    color: stat.color,
                  }}
                >
                  {stat.icon}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {stat.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="textSecondary">
                  {stat.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          System Information
        </Typography>
        {health && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="textSecondary">
                Status
              </Typography>
              <Typography variant="body1" fontWeight="bold">
                {health.status}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="textSecondary">
                Version
              </Typography>
              <Typography variant="body1">{health.version}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="textSecondary">
                Database
              </Typography>
              <Typography variant="body1">
                {health.database_connected ? 'Connected' : 'Disconnected'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="textSecondary">
                Redis
              </Typography>
              <Typography variant="body1">
                {health.redis_connected ? 'Connected' : 'Disconnected'}
              </Typography>
            </Grid>
          </Grid>
        )}
      </Paper>

      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quick Start
        </Typography>
        <Typography variant="body2" paragraph>
          1. Navigate to <strong>Generate Data</strong> to create synthetic patient records
        </Typography>
        <Typography variant="body2" paragraph>
          2. Use <strong>Privacy Management</strong> to apply differential privacy
        </Typography>
        <Typography variant="body2" paragraph>
          3. Download and analyze your privacy-preserving synthetic datasets
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Button variant="contained" href="/generate">
            Start Generating Data
          </Button>
        </Box>
      </Paper>
    </Layout>
  );
}

export default Dashboard;
