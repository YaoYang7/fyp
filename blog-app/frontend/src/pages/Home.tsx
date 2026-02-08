import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import Register from "../components/Register";
import Login from "../components/Login";
import LandingComponent from "../components/Landing";

type ContentKey = "home" | "register" | "login";

const HomePage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [currentContent, setCurrentContent] = useState<ContentKey>("home");

    useEffect(() => {
        const view = searchParams.get('view');
        if (view === 'register' || view === 'login') {
            setCurrentContent(view as ContentKey);
        } else {
            setCurrentContent('home');
        }
    }, [searchParams]);

    const loginPath = "/home?view=login";
    const registerPath = "/home?view=register";

    const renderCurrentContent = () => {
        switch (currentContent) {
            case "home":
                return <LandingComponent
                            onSwitchToLogin={() => navigate(loginPath)}
                            onSwitchToRegister={() => navigate(registerPath)}
                        />;
            case "register":
                return <Register onSwitchToLogin={() => navigate(loginPath)}/>;
            case "login":
                return (
                    <Login
                        onSwitchToRegister={() => navigate(registerPath)}
                        onLoginSuccess={() => navigate("/home")}
                    />
                );
            default:
                return <LandingComponent
                            onSwitchToLogin={() => navigate(loginPath)}
                            onSwitchToRegister={() => navigate(registerPath)}
                        />;
        }
    };

    return renderCurrentContent();
};

export default HomePage;
