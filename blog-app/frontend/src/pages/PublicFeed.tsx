import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Divider,
  Stack,
} from '@mui/material';
import {
  Article as ArticleIcon,
  Visibility,
  Login as LoginIcon,
} from '@mui/icons-material';
import { dashboardApi } from '../services/dashboardAPI';
import type { PublicPost, PublicTenant } from '../services/dashboardAPI';
import SafeHTML from '../components/SafeHTML';
import * as styles from './GroupBlogFeedsStyles';

const PublicFeed: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [posts, setPosts] = useState<PublicPost[]>([]);
  const [tenants, setTenants] = useState<PublicTenant[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<number | undefined>(undefined);

  const fetchData = async (tenantId?: number) => {
    try {
      setLoading(true);
      setError('');
      const [postsData, tenantsData] = await Promise.all([
        dashboardApi.getPublicPosts(tenantId),
        tenants.length === 0 ? dashboardApi.getPublicTenants() : Promise.resolve(tenants),
      ]);
      setPosts(postsData);
      if (tenants.length === 0) setTenants(tenantsData as PublicTenant[]);
    } catch (err) {
      console.error('Error fetching public feed:', err);
      setError('Failed to load posts. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTenantFilter = (tenantId?: number) => {
    setSelectedTenantId(tenantId);
    fetchData(tenantId);
  };

  if (loading) {
    return (
      <Box sx={styles.loadingContainer}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={styles.pageContainer}>
      {error && (
        <Alert severity="error" sx={styles.errorAlert} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={styles.paper}>
        <Box sx={styles.headerRow}>
          <Typography variant="h6">Explore Posts</Typography>
          <Button
            variant="contained"
            size="small"
            startIcon={<LoginIcon />}
            onClick={() => navigate('/home')}
          >
            Login / Register
          </Button>
        </Box>

        {tenants.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
              Filter by group:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 0.5 }}>
              <Chip
                label="All Groups"
                onClick={() => handleTenantFilter(undefined)}
                color={selectedTenantId === undefined ? 'primary' : 'default'}
                variant={selectedTenantId === undefined ? 'filled' : 'outlined'}
                size="small"
              />
              {tenants.map((tenant) => (
                <Chip
                  key={tenant.id}
                  label={tenant.name}
                  onClick={() => handleTenantFilter(tenant.id)}
                  color={selectedTenantId === tenant.id ? 'primary' : 'default'}
                  variant={selectedTenantId === tenant.id ? 'filled' : 'outlined'}
                  size="small"
                />
              ))}
            </Stack>
          </Box>
        )}

        <Divider sx={styles.divider} />

        {posts.length === 0 ? (
          <Typography variant="body1" color="text.secondary" sx={styles.emptyMessage}>
            No published posts yet.
          </Typography>
        ) : (
          <List>
            {posts.map((post, index) => (
              <ListItem
                key={post.id}
                sx={index < posts.length - 1 ? styles.listItemBorder : styles.listItemLast}
              >
                <ListItemAvatar>
                  <Avatar sx={styles.avatar}>
                    <ArticleIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={styles.postTitleRow}>
                      <Typography variant="subtitle1">{post.title}</Typography>
                      <Chip label={post.tenant_name} size="small" variant="outlined" />
                    </Box>
                  }
                  secondary={
                    <Box sx={styles.secondaryContent}>
                      {post.summary && (
                        <Typography variant="body2" color="text.secondary" sx={styles.summaryText}>
                          {post.summary}
                        </Typography>
                      )}
                      <Box sx={styles.contentPreview}>
                        <SafeHTML html={post.content} />
                      </Box>
                      <Box sx={styles.metaRow}>
                        <Typography variant="caption" color="text.secondary">
                          By <strong>{post.author}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {post.date}
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Visibility />}
                  onClick={() => navigate(`/explore/post/${post.id}`)}
                  sx={styles.viewButton}
                >
                  View
                </Button>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default PublicFeed;
