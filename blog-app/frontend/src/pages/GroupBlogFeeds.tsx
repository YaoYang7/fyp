import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import {
  Article as ArticleIcon,
} from '@mui/icons-material';
import { dashboardApi } from '../services/dashboardAPI';
import type { BlogPost } from '../services/dashboardAPI';

const GroupBlogFeeds: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [posts, setPosts] = useState<BlogPost[]>([]);

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        setLoading(true);
        setError('');
        const data = await dashboardApi.getFeedPosts();
        setPosts(data);
      } catch (err) {
        console.error('Error fetching feed:', err);
        setError('Failed to load feed. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchFeed();
  }, []);

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        {posts.length === 0 ? (
          <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
            No published posts yet. Be the first to publish!
          </Typography>
        ) : (
          <List>
            {posts.map((post, index) => (
              <ListItem
                key={post.id}
                sx={{
                  borderBottom: index < posts.length - 1 ? '1px solid #e0e0e0' : 'none',
                  px: 0,
                }}
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: '#1976d2' }}>
                    <ArticleIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">{post.title}</Typography>
                      <Chip
                        label={post.status}
                        size="small"
                        color="success"
                      />
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {post.summary}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
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
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
};

export default GroupBlogFeeds;
