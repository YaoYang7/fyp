import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Button,
} from '@mui/material';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { logout } from '../store/auth/authActions';
import AccountInfo from './AccountInfo';

const drawerWidth = 240;

const navigationItems = [
  { label: 'Home', path: '/home', requiresAuth: false },
  { label: 'Dashboard', path: '/dashboard', requiresAuth: true },
  { label: 'Register', path: '/home?view=register', requiresAuth: false, authOnly: false },
  { label: 'Login', path: '/home?view=login', requiresAuth: false, authOnly: false },
] as const;

interface SidePanelLayoutProps {
  children: React.ReactNode;
}

const SidePanelLayout: React.FC<SidePanelLayoutProps> = ({ children }) => {
  const { isLoggedIn, user } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const handleLogout = () => {
    // Clear the JWT token from localStorage
    localStorage.removeItem('authToken');
    dispatch(logout());
    navigate('/home');
  };

  const isCurrentPath = (path: string) => {
    const currentPath = location.pathname + location.search;

    if (path.includes('?')) {
      // For paths with query params, match the full URL
      return currentPath === path;
    }

    // For paths without query params, ensure current URL also has no query params
    return currentPath === path && !location.search;
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, textAlign: 'center' }}>
            Blog Application / Platform
          </Typography>
          {isLoggedIn && user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body1" sx={{ color: 'white' }}>
                Welcome, {user.username}
              </Typography>
              <Button
                color="inherit"
                onClick={handleLogout}
                sx={{ textTransform: 'none' }}
              >
                Logout
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', display: 'flex', flexDirection: 'column', height: '100%' }}>
          {isLoggedIn && <AccountInfo />}
          <List>
            {navigationItems
              .filter((item) => {
                // Hide Home, Login and Register when user is logged in
                if (isLoggedIn && (item.label === 'Home' || item.label === 'Login' || item.label === 'Register')) {
                  return false;
                }
                // Hide Dashboard when user is not logged in
                if (!isLoggedIn && item.requiresAuth) {
                  return false;
                }
                return true;
              })
              .map((item) => (
                <ListItem key={item.label} disablePadding>
                  <ListItemButton
                    selected={isCurrentPath(item.path)}
                    onClick={() => handleNavigation(item.path)}
                  >
                    <ListItemText primary={item.label} />
                  </ListItemButton>
                </ListItem>
              ))}
            {isLoggedIn && (
              <ListItem disablePadding>
                <ListItemButton onClick={handleLogout}>
                  <ListItemText primary="Logout" />
                </ListItemButton>
              </ListItem>
            )}
          </List>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default SidePanelLayout;
