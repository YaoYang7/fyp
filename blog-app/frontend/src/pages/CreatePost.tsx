import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  TextField,
  Button,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { dashboardApi } from '../services/dashboardAPI';
import type { CreatePostData } from '../services/dashboardAPI';

const CreatePost: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [formData, setFormData] = useState<CreatePostData>({
    title: '',
    content: '',
    summary: '',
    status: 'draft',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.title.trim()) {
      setError('Title is required.');
      return;
    }
    if (!formData.content.trim()) {
      setError('Content is required.');
      return;
    }

    try {
      setLoading(true);
      await dashboardApi.createPost(formData);
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Error creating post:', err);
      const message = err.response?.data?.detail || 'Failed to create post. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            label="Title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            fullWidth
          />

          <TextField
            label="Summary"
            name="summary"
            value={formData.summary}
            onChange={handleChange}
            fullWidth
            placeholder="A short summary of your post (optional)"
          />

          <TextField
            label="Content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            required
            fullWidth
            multiline
            minRows={10}
          />

          <TextField
            label="Status"
            name="status"
            value={formData.status}
            onChange={handleChange}
            select
            fullWidth
          >
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="published">Published</MenuItem>
          </TextField>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/dashboard')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Creating...' : 'Create Post'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default CreatePost;
