import React, { useState } from "react";
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
} from "@mui/material";
import Register from "../components/Register";
import Login from "../components/Login";
import LandingComponent from "../components/Landing";
import { useAppSelector } from "../store/hooks";

const drawerWidth = 240;

const sidePanelItems = [
  { label: "Home", key: "home" },
  { label: "Register", key: "register" },
  { label: "Login", key: "login" },
] as const;

type ContentKey = "home" | "register" | "login";

const HomePage: React.FC = () => {
    const { isLoggedIn, user } = useAppSelector((state) => state.auth);
    const [currentContent, setCurrentContent] = useState<ContentKey>("home");

    const renderCurrentContent = () => {
        switch (currentContent) {
            case "home":
                return (
                    <LandingComponent />
                );
            case "register":
                return (
                    <>
                        <Typography variant="h4" gutterBottom>Register</Typography>
                        <Register onSwitchToLogin={() => setCurrentContent("login")}/>
                    </>
                );
            case "login":
                return (
                    <>
                        <Typography variant="h4" gutterBottom>Login</Typography>
                        <Login
                            onSwitchToRegister={() => setCurrentContent("register")}
                            onLoginSuccess={() => setCurrentContent("home")}
                        />
                    </>
                );
            default:
                return (
                    <LandingComponent />
                );
        }
    };

    return (
        <Box sx={{ display: "flex" }}>
            <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
                <Toolbar>
                    <Typography variant="h6" sx={{ flexGrow: 1, textAlign: "center" }}>Blog Application / Platform</Typography>
                    {isLoggedIn && user && (
                        <Typography variant="body1" sx={{ color: 'white' }}>
                            Welcome, {user.username}
                        </Typography>
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
                        boxSizing: "border-box",
                    },
                }}
            >
                <Toolbar />
                <Box sx={{ overflow: "auto" }}>
                    <List>
                        {sidePanelItems
                            .filter((item) => {
                                // Hide Login and Register when user is logged in
                                if (isLoggedIn && (item.key === 'login' || item.key === 'register')) {
                                    return false;
                                }
                                return true;
                            })
                            .map((item) => (
                            <ListItem key={item.key} disablePadding>
                                <ListItemButton selected={currentContent === item.key}onClick={() => setCurrentContent(item.key)}>
                                    <ListItemText primary={item.label} />
                                </ListItemButton>
                            </ListItem>
                        ))}
                    </List>
                </Box>
            </Drawer>

            <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                <Toolbar />
                {renderCurrentContent()}
            </Box>
        </Box>
    );
};

export default HomePage;
