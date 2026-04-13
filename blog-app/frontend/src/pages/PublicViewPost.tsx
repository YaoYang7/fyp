import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  TextField,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
  Tooltip,
} from '@mui/material';
import { ArrowBack, CalendarToday, Login as LoginIcon, Delete, Comment as CommentIcon } from '@mui/icons-material';
import { dashboardApi } from '../services/dashboardAPI';
import type { PublicPost, Comment } from '../services/dashboardAPI';
import SafeHTML from '../components/SafeHTML';
import * as styles from './ViewPostStyles';

const PublicViewPost: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isLoggedIn = useSelector((state: RootState) => state.auth.isLoggedIn);
  const currentUser = useSelector((state: RootState) => state.auth.user);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [post, setPost] = useState<PublicPost | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  useEffect(() => {
    const fetchPost = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError('');
        const [data, commentsData] = await Promise.all([
          dashboardApi.getPublicPost(Number(id)),
          dashboardApi.getPublicPostComments(Number(id)),
        ]);
        setPost(data);
        setComments(commentsData);
      } catch (err: any) {
        console.error('Error fetching post:', err);
        setError(err.response?.data?.detail || 'Failed to load post.');
      } finally {
        setLoading(false);
      }
    };
    fetchPost();
  }, [id]);

  const handleSubmitComment = async () => {
    if (!commentText.trim() || !post) return;
    try {
      setSubmittingComment(true);
      const newComment = await dashboardApi.createComment(post.id, commentText.trim());
      setComments((prev) => [newComment, ...prev]);
      setCommentText('');
    } catch (err: any) {
      console.error('Error submitting comment:', err);
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!post) return;
    try {
      await dashboardApi.deleteComment(post.id, commentId);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
    } catch (err: any) {
      console.error('Error deleting comment:', err);
    }
  };

  const canComment = isLoggedIn && post && currentUser?.tenant_id === post.tenant_id;

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
      </Paper>

      <Box sx={styles.commentsSection}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <CommentIcon color="action" />
          <Typography variant="h6">Comments ({comments.length})</Typography>
        </Box>
        <Divider sx={styles.divider} />

        {comments.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            No comments yet.
          </Typography>
        ) : (
          <List disablePadding>
            {comments.map((comment) => (
              <ListItem key={comment.id} sx={styles.commentItem}>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    {comment.author.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={styles.commentHeader}>
                      <Typography variant="subtitle2">{comment.author}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(comment.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                  secondary={comment.content}
                />
                {currentUser && comment.author_id === currentUser.id && (
                  <Tooltip title="Delete comment">
                    <IconButton size="small" onClick={() => handleDeleteComment(comment.id)} color="error">
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </ListItem>
            ))}
          </List>
        )}

        {canComment ? (
          <>
            <TextField
              fullWidth
              multiline
              minRows={2}
              placeholder="Write a comment..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              sx={styles.commentTextField}
            />
            <Box sx={styles.commentSubmitRow}>
              <Button
                variant="contained"
                onClick={handleSubmitComment}
                disabled={submittingComment || !commentText.trim()}
                sx={styles.commentSubmitButton}
              >
                {submittingComment ? 'Submitting...' : 'Submit Comment'}
              </Button>
            </Box>
          </>
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {isLoggedIn ? 'Join this group to comment.' : 'Want to join the conversation?'}
            </Typography>
            {!isLoggedIn && (
              <Button
                variant="contained"
                size="small"
                startIcon={<LoginIcon />}
                onClick={() => navigate('/home')}
              >
                Login / Register
              </Button>
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default PublicViewPost;
