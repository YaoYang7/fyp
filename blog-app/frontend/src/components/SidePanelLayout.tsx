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
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import { DarkMode, LightMode } from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { useThemeContext } from '../theme/ThemeContext';
import { logout } from '../store/auth/authActions';
import AccountInfo from './AccountInfo';
import LoggedInActions from './LoggedInActions';

const drawerWidth = 240;

const navigationItems = [
  { label: 'Home', path: '/home', requiresAuth: false },
  { label: 'Explore Posts', path: '/explore', requiresAuth: false },
  { label: 'Dashboard', path: '/dashboard', requiresAuth: true },
  { label: 'Create New Post', path: '/create_post', requiresAuth: true },
  { label: 'Manage Posts', path: '/manage_blog', requiresAuth: true },
  { label: 'Group Posts', path: '/feed', requiresAuth: true },
  { label: 'Group Users', path: '/group_users', requiresAuth: true },
  { label: 'Account Info', path: '/account_info', requiresAuth: true },
  { label: 'Register', path: '/home?view=register', requiresAuth: false, authOnly: false },
  { label: 'Login', path: '/home?view=login', requiresAuth: false, authOnly: false },
] as const;

const PAGE_TITLES: Record<string, string> = {
  '/explore': 'Explore Posts',
  '/dashboard': 'Dashboard',
  '/create_post': 'Create Post',
  '/manage_blog': 'Manage Posts',
  '/feed': 'Group Posts',
  '/group_users': 'Group Users',
  '/account_info': 'Account Info',
};

const getPageTitle = (pathname: string, search: string): string => {
  switch (true) {
    case pathname.startsWith('/edit_post'): 
      return 'Edit Post';
    case !!PAGE_TITLES[pathname]:           
      return PAGE_TITLES[pathname];
    case search === '?view=login':          
      return 'Login';
    case search === '?view=register':       
      return 'Register';
    default:                                
      return 'Blog Application / Platform';
  }
};

interface SidePanelLayoutProps {
  children: React.ReactNode;
}

const SidePanelLayout: React.FC<SidePanelLayoutProps> = ({ children }) => {
  const { isLoggedIn } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { mode, toggleTheme } = useThemeContext();

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

    // Highlight Manage Posts when editing a post
    if (path === '/manage_blog' && location.pathname.startsWith('/edit_post')) {
      return true;
    }

    // For paths without query params, ensure current URL also has no query params
    return currentPath === path && !location.search;
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, textAlign: 'center' }}>
            {getPageTitle(location.pathname, location.search)}
          </Typography>
          <Tooltip title={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
            <IconButton color="inherit" onClick={toggleTheme}>
              {mode === 'light' ? <DarkMode /> : <LightMode />}
            </IconButton>
          </Tooltip>
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
          {isLoggedIn ? <AccountInfo /> : null}
          {isLoggedIn ? <Divider sx={{ my: 2 }} /> : null}
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
          </List>
          {isLoggedIn ? <LoggedInActions onLogout={handleLogout} /> : null}
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
