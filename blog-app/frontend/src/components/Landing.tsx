import {
    Box,
    Typography,
    Button,
    Container,
    Card,
    CardContent,
    Stack
} from "@mui/material";
import CreateIcon from "@mui/icons-material/Create";
import PeopleIcon from "@mui/icons-material/People";
import DashboardIcon from "@mui/icons-material/Dashboard";

interface LandingProps {
    onSwitchToLogin: () => void;
    onSwitchToRegister: () => void;
}

const LandingComponent: React.FC<LandingProps> = (props) => {

    const features = [
        {
            icon: <CreateIcon sx={{ fontSize: 48, color: "primary.main" }} />,
            title: "Create & Publish",
            description:
                "Write and publish your blog posts with an intuitive editor. Share your thoughts with the world in minutes."
        },
        {
            icon: <PeopleIcon sx={{ fontSize: 48, color: "primary.main" }} />,
            title: "Multi-Tenant",
            description:
                "Each user gets their own space. Manage multiple blogs from a single platform with complete isolation."
        },
        {
            icon: <DashboardIcon sx={{ fontSize: 48, color: "primary.main" }} />,
            title: "Easy Management",
            description:
                "Powerful dashboard to manage your content, track engagement, and grow your audience effortlessly."
        },
    ];

    return (
        <Box>
            {/* Hero Section */}
            <Box
                sx={{
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    color: "white",
                    py: 12,
                    minHeight: "70vh",
                    display: "flex",
                    alignItems: "center"
                }}
            >
                <Container maxWidth="lg">
                    <Box
                        sx={{
                            display: "grid",
                            gridTemplateColumns: {
                                xs: "1fr",
                                md: "7fr 5fr"
                            },
                            gap: 4,
                            alignItems: "center"
                        }}
                    >
                        <Box>
                            <Typography
                                variant="h2"
                                component="h1"
                                gutterBottom
                                sx={{ fontWeight: 700, mb: 3 }}
                            >
                                Post your ideas to the platform.
                            </Typography>

                            <Typography
                                variant="h5"
                                sx={{ mb: 4, opacity: 0.95, fontWeight: 300 }}
                            >
                                Start your blogging journey today. Create, publish,
                                and share your ideas with a platform built for modern
                                content creators.
                            </Typography>

                            <Stack direction="row" spacing={2}>
                                <Button
                                    variant="contained"
                                    size="large"
                                    onClick={props.onSwitchToRegister}
                                    sx={{
                                        bgcolor: "white",
                                        color: "primary.main",
                                        fontWeight: 600,
                                        px: 4,
                                        py: 1.5,
                                        "&:hover": {
                                            bgcolor: "rgba(255, 255, 255, 0.9)"
                                        }
                                    }}
                                >
                                    Register
                                </Button>

                                <Button
                                    variant="outlined"
                                    size="large"
                                    onClick={props.onSwitchToLogin}
                                    sx={{
                                        borderColor: "white",
                                        color: "white",
                                        fontWeight: 600,
                                        px: 4,
                                        py: 1.5,
                                        "&:hover": {
                                            borderColor: "white",
                                            bgcolor: "rgba(255, 255, 255, 0.1)"
                                        }
                                    }}
                                >
                                    Login
                                </Button>
                            </Stack>
                        </Box>
                    </Box>
                </Container>
            </Box>

            {/* Features Section */}
            <Container maxWidth="lg" sx={{ py: 10 }}>
                <Typography
                    variant="h3"
                    align="center"
                    gutterBottom
                    sx={{ fontWeight: 600, mb: 2 }}
                >
                    Everything You Need to Blog
                </Typography>

                <Typography
                    variant="h6"
                    align="center"
                    color="text.secondary"
                    sx={{ mb: 6 }}
                >
                    Powerful features designed for content creators
                </Typography>

                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            md: "repeat(3, 1fr)"
                        },
                        gap: 4
                    }}
                >
                    {features.map((feature, index) => (
                        <Card
                            key={index}
                            sx={{
                                height: "100%",
                                textAlign: "center",
                                transition: "transform 0.2s",
                                "&:hover": {
                                    transform: "translateY(-8px)",
                                    boxShadow: 4
                                }
                            }}
                        >
                            <CardContent sx={{ p: 4 }}>
                                <Box sx={{ mb: 2 }}>{feature.icon}</Box>

                                <Typography
                                    variant="h6"
                                    gutterBottom
                                    sx={{ fontWeight: 600 }}
                                >
                                    {feature.title}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {feature.description}
                                </Typography>
                            </CardContent>
                        </Card>
                    ))}
                </Box>
            </Container>

            {/* CTA Section */}
            <Box sx={{ bgcolor: "grey.100", py: 10 }}>
                <Container maxWidth="md">
                    <Box textAlign="center">
                        <Typography
                            variant="h3"
                            gutterBottom
                            sx={{ fontWeight: 600, mb: 2 }}
                        >
                            Start Blogging?
                        </Typography>

                        <Button
                            variant="contained"
                            size="large"
                            onClick={props.onSwitchToRegister}
                            sx={{
                                px: 5,
                                py: 2,
                                fontWeight: 600,
                                fontSize: "1.1rem"
                            }}
                        >
                            Register!
                        </Button>
                    </Box>
                </Container>
            </Box>
        </Box>
    );
};

export default LandingComponent;
