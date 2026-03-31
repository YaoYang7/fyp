import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import { ArrowBack, CalendarToday, Login as LoginIcon } from '@mui/icons-material';
import { dashboardApi } from '../services/dashboardAPI';
import type { PublicPost } from '../services/dashboardAPI';
import SafeHTML from '../components/SafeHTML';
import * as styles from './ViewPostStyles';

const PublicViewPost: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [post, setPost] = useState<PublicPost | null>(null);

  useEffect(() => {
    const fetchPost = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError('');
        const data = await dashboardApi.getPublicPost(Number(id));
        setPost(data);
      } catch (err: any) {
        console.error('Error fetching post:', err);
        setError(err.response?.data?.detail || 'Failed to load post.');
      } finally {
        setLoading(false);
      }
    };
    fetchPost();
  }, [id]);

  if (loading) {
    return (
      <Box sx={styles.loadingContainer}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={styles.pageContainer}>
        <Alert severity="error" sx={styles.errorAlert}>{error}</Alert>
        <Button variant="outlined" startIcon={<ArrowBack />} onClick={() => navigate('/explore')}>
          Back to Explore
        </Button>
      </Box>
    );
  }

  if (!post) return null;

  return (
    <Box sx={styles.pageContainer}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/explore')}
        sx={styles.backButton}
      >
        Back to Explore
      </Button>

      <Paper sx={styles.paper}>
        <Typography variant="h4" sx={styles.title}>
          {post.title}
        </Typography>

        <Box sx={styles.metaRow}>
          <Typography variant="body2" color="text.secondary">
            By <strong>{post.author}</strong>
          </Typography>
          <Chip label={post.tenant_name} size="small" variant="outlined" />
          <Box sx={styles.metaIconGroup}>
            <CalendarToday sx={styles.metaIcon} />
            <Typography variant="body2" color="text.secondary">
              {post.date}
            </Typography>
          </Box>
        </Box>

        {post.summary && (
          <Typography variant="subtitle1" color="text.secondary" sx={styles.summary}>
            {post.summary}
          </Typography>
        )}

        <Divider sx={styles.divider} />

        <Box sx={styles.contentArea}>
          <SafeHTML html={post.content} />
        </Box>

        <Divider sx={{ mt: 4, mb: 2 }} />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Want to join the conversation?
          </Typography>
          <Button
            variant="contained"
            size="small"
            startIcon={<LoginIcon />}
            onClick={() => navigate('/home')}
          >
            Login / Register
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default PublicViewPost;
