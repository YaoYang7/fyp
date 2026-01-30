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

const drawerWidth = 240;

const navigationItems = [
  { label: 'Home', path: '/home', requiresAuth: false },
  { label: 'Dashboard', path: '/dashboard', requiresAuth: true },
  { label: 'Register', path: '/home?view=register', requiresAuth: false, authOnly: false },
  { label: 'Login', path: '/home?view=login', requiresAuth: false, authOnly: false },
] as const;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isLoggedIn, user } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/home');
  };

  const isCurrentPath = (path: string) => {
    if (path.includes('?')) {
      const [basePath] = path.split('?');
      return location.pathname === basePath;
    }
    return location.pathname === path;
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
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {navigationItems
              .filter((item) => {
                // Hide Login and Register when user is logged in
                if (isLoggedIn && (item.label === 'Login' || item.label === 'Register')) {
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

export default Layout;