import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
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
  IconButton,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Tooltip,
} from '@mui/material';
import { ArrowBack, CalendarToday, Delete, Comment as CommentIcon } from '@mui/icons-material';
import { dashboardApi } from '../services/dashboardAPI';
import type { BlogPost, Comment } from '../services/dashboardAPI';
import type { RootState } from '../store/store';
import SafeHTML from '../components/SafeHTML';
import * as styles from './ViewPostStyles';
import {
  VARIANT_OUTLINED, VARIANT_TEXT, VARIANT_CONTAINED,
  VARIANT_H4, VARIANT_H6, VARIANT_BODY2, VARIANT_SUBTITLE1, VARIANT_SUBTITLE2, VARIANT_CAPTION,
  COLOR_TEXT_SECONDARY, COLOR_SUCCESS, COLOR_ACTION, COLOR_ERROR, COLOR_PRIMARY_MAIN,
  SIZE_SMALL,
} from './COMMON_CONSTANTS';

const FEED_ROUTE = '/feed';
const FALLBACK_ERROR_MSG = 'Failed to load post.';
const NO_COMMENTS_MSG = 'No comments yet. Be the first to comment!';
const COMMENT_PLACEHOLDER = 'Write a comment...';
const DELETE_TOOLTIP = 'Delete comment';
const BACK_LABEL = 'Back to Feed';
const SUBMIT_LABEL = 'Submit Comment';
const SUBMITTING_LABEL = 'Submitting...';

const ViewPost: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [post, setPost] = useState<BlogPost | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  const currentUser = useSelector((state: RootState) => state.auth.user);

  useEffect(() => {
    const fetchPostAndComments = async () => {
      if (!id) return;
      try {
        setLoading(true);
        setError('');
        const [postData, commentsData] = await Promise.all([
          dashboardApi.getPost(Number(id)),
          dashboardApi.getPostComments(Number(id)),
        ]);
        setPost(postData);
        setComments(commentsData);
      } catch (err: any) {
        console.error('Error fetching post:', err);
        const message = err.response?.data?.detail || FALLBACK_ERROR_MSG;
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchPostAndComments();
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
        <Alert severity="error" sx={styles.errorAlert}>
          {error}
        </Alert>
        <Button
          variant={VARIANT_OUTLINED}
          startIcon={<ArrowBack />}
          onClick={() => navigate(FEED_ROUTE)}
        >
          {BACK_LABEL}
        </Button>
      </Box>
    );
  }

  if (!post) return null;

  return (
    <Box sx={styles.pageContainer}>
      <Button
        variant={VARIANT_TEXT}
        startIcon={<ArrowBack />}
        onClick={() => navigate(FEED_ROUTE)}
        sx={styles.backButton}
      >
        {BACK_LABEL}
      </Button>

      <Paper sx={styles.paper}>
        <Typography variant={VARIANT_H4} sx={styles.title}>
          {post.title}
        </Typography>

        <Box sx={styles.metaRow}>
          <Typography variant={VARIANT_BODY2} color={COLOR_TEXT_SECONDARY}>
            By <strong>{post.author}</strong>
          </Typography>
          <Box sx={styles.metaIconGroup}>
            <CalendarToday sx={styles.metaIcon} />
            <Typography variant={VARIANT_BODY2} color={COLOR_TEXT_SECONDARY}>
              {post.date}
            </Typography>
          </Box>
          <Chip label={post.status} size={SIZE_SMALL} color={COLOR_SUCCESS} />
        </Box>

        {post.summary && (
          <Typography variant={VARIANT_SUBTITLE1} color={COLOR_TEXT_SECONDARY} sx={styles.summary}>
            {post.summary}
          </Typography>
        )}

        <Divider sx={styles.divider} />

        <Box sx={styles.contentArea}>
          <SafeHTML html={post.content} />
        </Box>
      </Paper>

      {/* Comments Section */}
      <Box sx={styles.commentsSection}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <CommentIcon color={COLOR_ACTION} />
          <Typography variant={VARIANT_H6}>
            Comments ({comments.length})
          </Typography>
        </Box>
        <Divider sx={styles.divider} />

        {comments.length === 0 ? (
          <Typography variant={VARIANT_BODY2} color={COLOR_TEXT_SECONDARY} sx={{ mb: 2 }}>
            {NO_COMMENTS_MSG}
          </Typography>
        ) : (
          <List disablePadding>
            {comments.map((comment) => (
              <ListItem key={comment.id} sx={styles.commentItem}>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: COLOR_PRIMARY_MAIN }}>
                    {comment.author.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={styles.commentHeader}>
                      <Typography variant={VARIANT_SUBTITLE2}>{comment.author}</Typography>
                      <Typography variant={VARIANT_CAPTION} color={COLOR_TEXT_SECONDARY}>
                        {new Date(comment.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                  }
                  secondary={comment.content}
                />
                {currentUser && comment.author_id === currentUser.id && (
                  <Tooltip title={DELETE_TOOLTIP}>
                    <IconButton
                      size={SIZE_SMALL}
                      onClick={() => handleDeleteComment(comment.id)}
                      color={COLOR_ERROR}
                    >
                      <Delete fontSize={SIZE_SMALL} />
                    </IconButton>
                  </Tooltip>
                )}
              </ListItem>
            ))}
          </List>
        )}

        {/* New comment form */}
        <TextField
          fullWidth
          multiline
          minRows={2}
          placeholder={COMMENT_PLACEHOLDER}
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          sx={styles.commentTextField}
        />
        <Box sx={styles.commentSubmitRow}>
          <Button
            variant={VARIANT_CONTAINED}
            onClick={handleSubmitComment}
            disabled={submittingComment || !commentText.trim()}
            sx={styles.commentSubmitButton}
          >
            {submittingComment ? SUBMITTING_LABEL : SUBMIT_LABEL}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default ViewPost;
