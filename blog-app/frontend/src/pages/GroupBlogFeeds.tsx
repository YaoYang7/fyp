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
} from '@mui/material';
import {
  Article as ArticleIcon,
  Visibility,
  Refresh,
} from '@mui/icons-material';
import { dashboardApi } from '../services/dashboardAPI';
import type { BlogPost } from '../services/dashboardAPI';
import SafeHTML from '../components/SafeHTML';
import * as styles from './GroupBlogFeedsStyles';

const GroupBlogFeeds: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string>('');
  const [posts, setPosts] = useState<BlogPost[]>([]);

  const fetchFeed = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError('');
      const data = await dashboardApi.getFeedPosts();
      setPosts(data);
    } catch (err) {
      console.error('Error fetching feed:', err);
      setError('Failed to load feed. Please try again later.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFeed();
  }, []);

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
          <Typography variant="h6">Recent Group Posts</Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={refreshing ? <CircularProgress size={16} /> : <Refresh />}
            onClick={() => fetchFeed(true)}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
        <Divider sx={styles.divider} />
        {posts.length === 0 ? (
          <Typography variant="body1" color="text.secondary" sx={styles.emptyMessage}>
            No published posts yet. Be the first to publish!
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
                      <Chip
                        label={post.status}
                        size="small"
                        color="success"
                      />
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
                  onClick={() => navigate(`/post/${post.id}`)}
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

export default GroupBlogFeeds;
