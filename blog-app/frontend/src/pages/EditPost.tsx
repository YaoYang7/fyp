import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
import type { UpdatePostData } from '../services/dashboardAPI';
import RichTextEditor from '../components/editor/RichTextEditor';

const EditPost: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [formData, setFormData] = useState<UpdatePostData>({
    title: '',
    content: '',
    summary: '',
    status: 'draft',
  });

  useEffect(() => {
    const fetchPost = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError('');
        const post = await dashboardApi.getPost(Number(id));
        setFormData({
          title: post.title,
          content: post.content,
          summary: post.summary || '',
          status: post.status,
        });
      } catch (err: any) {
        console.error('Error fetching post:', err);
        const message = err.response?.data?.detail || 'Failed to load post.';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.title?.trim()) {
      setError('Title is required.');
      return;
    }
    if (!formData.content || formData.content === '<p></p>') {
      setError('Content is required.');
      return;
    }

    try {
      setSaving(true);
      await dashboardApi.updatePost(Number(id), formData);
      navigate('/manage_blog');
    } catch (err: any) {
      console.error('Error updating post:', err);
      const message = err.response?.data?.detail || 'Failed to update post. Please try again.';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

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

          <RichTextEditor
            content={formData.content || ''}
            onChange={(html) => setFormData((prev) => ({ ...prev, content: html }))}
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
              onClick={() => navigate('/manage_blog')}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={saving}
              startIcon={saving ? <CircularProgress size={20} /> : null}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default EditPost;
