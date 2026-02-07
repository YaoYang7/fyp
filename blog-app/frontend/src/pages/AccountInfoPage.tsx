import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  CalendarToday as CalendarIcon,
  Badge as BadgeIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useAppSelector } from '../store/hooks';

const AccountInfoPage: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);

  if (!user) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 2 }}>
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
          <Avatar sx={{ width: 100, height: 100, mb: 2, bgcolor: 'primary.main', fontSize: 40 }}>
            <PersonIcon sx={{ fontSize: 60 }} />
          </Avatar>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {user.username}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            User ID: {user.id}
          </Typography>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Account Details
        </Typography>

        <List>
          <ListItem>
            <ListItemIcon>
              <BadgeIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Username"
              secondary={user.username}
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <EmailIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Email"
              secondary={user.email}
            />
          </ListItem>

          {user.tenant_name && (
            <ListItem>
              <ListItemIcon>
                <BusinessIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="Organisation"
                secondary={user.tenant_name}
              />
            </ListItem>
          )}

          <ListItem>
            <ListItemIcon>
              <BusinessIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Organisation ID"
              secondary={user.tenant_id}
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <CalendarIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Member Since"
              secondary={formatDate(user.created_at)}
            />
          </ListItem>

          {user.updated_at ? (
            <ListItem>
              <ListItemIcon>
                <CalendarIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary="Last Updated"
                secondary={formatDate(user.updated_at)}
              />
            </ListItem>
          ) : null}
        </List>
      </Paper>
    </Box>
  );
};

export default AccountInfoPage;
