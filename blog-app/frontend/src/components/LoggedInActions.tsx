import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
} from '@mui/material';
import {
  Add as AddIcon,
  Article as ArticleIcon,
  Comment as CommentIcon,
} from '@mui/icons-material';

interface LoggedInActionsProps {
  onLogout: () => void;
}

const LoggedInActions: React.FC<LoggedInActionsProps> = ({ onLogout }) => {
  const navigate = useNavigate();

  return (
    <>
      <Divider sx={{ my: 2 }} />
      <Box sx={{ px: 2 }}>
        <List dense>
          <ListItem disablePadding>
            <ListItemButton sx={{ borderRadius: 1 }} onClick={() => navigate('/create_post')}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                <AddIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Create New Post" />
            </ListItemButton>
          </ListItem>
          <ListItem disablePadding>
            <ListItemButton sx={{ borderRadius: 1 }}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                <ArticleIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Manage Posts" />
            </ListItemButton>
          </ListItem>
          <ListItem disablePadding>
            <ListItemButton sx={{ borderRadius: 1 }}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                <CommentIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="View Comments" />
            </ListItemButton>
          </ListItem>
        </List>
      </Box>
      <Box sx={{ flexGrow: 1 }} />
      <Box sx={{ p: 2 }}>
        <Button
          variant="outlined"
          fullWidth
          onClick={onLogout}
          sx={{ textTransform: 'none' }}
        >
          Logout
        </Button>
      </Box>
    </>
  );
};

export default LoggedInActions;
