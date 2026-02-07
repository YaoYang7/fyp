import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  ToggleButton,
  ToggleButtonGroup,
  InputAdornment,
} from '@mui/material';
import {
  Article as ArticleIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { dashboardApi } from '../services/dashboardAPI';
import type { BlogPost } from '../services/dashboardAPI';

const ManageBlog: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [postToDelete, setPostToDelete] = useState<BlogPost | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await dashboardApi.getUserPosts();
      setPosts(data);
    } catch (err) {
      console.error('Error fetching posts:', err);
      setError('Failed to load posts. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      fetchPosts();
      return;
    }
    try {
      setLoading(true);
      setError('');
      const data = await dashboardApi.searchPosts(query);
      setPosts(data);
    } catch (err) {
      console.error('Error searching posts:', err);
      setError('Failed to search posts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusToggle = async (post: BlogPost) => {
    const newStatus = post.status === 'published' ? 'draft' : 'published';
    try {
      setActionLoading(post.id);
      await dashboardApi.updatePost(post.id, { status: newStatus });
      setPosts((prev) =>
        prev.map((p) => (p.id === post.id ? { ...p, status: newStatus } : p))
      );
    } catch (err) {
      console.error('Error updating post status:', err);
      setError('Failed to update post status.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteClick = (post: BlogPost) => {
    setPostToDelete(post);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!postToDelete) return;
    try {
      setActionLoading(postToDelete.id);
      await dashboardApi.deletePost(postToDelete.id);
      setPosts((prev) => prev.filter((p) => p.id !== postToDelete.id));
      setDeleteDialogOpen(false);
      setPostToDelete(null);
    } catch (err) {
      console.error('Error deleting post:', err);
      setError('Failed to delete post.');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'success';
      case 'draft':
        return 'warning';
      default:
        return 'default';
    }
  };

  const filteredPosts = posts.filter((post) => {
    if (statusFilter === 'all') return true;
    return post.status === statusFilter;
  });

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

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Manage Posts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{ textTransform: 'none' }}
          onClick={() => navigate('/create_post')}
        >
          New Post
        </Button>
      </Box>

      {/* Search and Filter */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          placeholder="Search posts..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          size="small"
          sx={{ minWidth: 250 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            },
          }}
        />
        <ToggleButtonGroup
          value={statusFilter}
          exclusive
          onChange={(_e, value) => { if (value !== null) setStatusFilter(value); }}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="published">Published</ToggleButton>
          <ToggleButton value="draft">Drafts</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Posts List */}
      <Paper sx={{ p: 3 }}>
        {filteredPosts.length === 0 ? (
          <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
            {searchQuery ? 'No posts match your search.' : 'No posts yet. Create your first post!'}
          </Typography>
        ) : (
          <List>
            {filteredPosts.map((post, index) => (
              <ListItem
                key={post.id}
                sx={{
                  borderBottom: index < filteredPosts.length - 1 ? '1px solid #e0e0e0' : 'none',
                  px: 0,
                }}
                secondaryAction={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={post.status === 'published' ? 'Published' : 'Draft'}
                      size="small"
                      color={getStatusColor(post.status) as any}
                      onClick={() => handleStatusToggle(post)}
                      disabled={actionLoading === post.id}
                      sx={{ cursor: 'pointer', minWidth: 80 }}
                    />
                    <IconButton
                      aria-label="edit"
                      onClick={() => navigate(`/edit_post/${post.id}`)}
                      disabled={actionLoading === post.id}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      aria-label="delete"
                      onClick={() => handleDeleteClick(post)}
                      disabled={actionLoading === post.id}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                }
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: '#1976d2' }}>
                    <ArticleIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Typography variant="subtitle1">{post.title}</Typography>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      {post.summary && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {post.summary}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        {post.date}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Post</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{postToDelete?.title}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ManageBlog;
