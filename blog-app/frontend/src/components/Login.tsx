import { Typography, Box, TextField, Paper, Button, Link, Alert } from "@mui/material";
import { useState } from "react";
import IconButton from "@mui/material/IconButton";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import { useAppDispatch } from "../store/hooks";
import { loginSuccess } from "../store/auth/authActions";


interface LoginProps {
  onSwitchToRegister: () => void;
  onLoginSuccess?: () => void;
}

const Login: React.FC<LoginProps> = (props) => {
  const dispatch = useAppDispatch();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/user_api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      dispatch(loginSuccess(data.user));
      console.log("Login successful:", data);

      // Navigate to home after successful login
      if (props.onLoginSuccess) {
        props.onLoginSuccess();
      }
    } catch (err: any) {
      setError(err.message || "An error occurred during login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',}}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: '500px', width: '100%' }}>
        <Typography variant="h4" gutterBottom>Login</Typography>
        <Typography variant="body2" sx={{ color: '#666', mb: 3 }}>
          Sign in to access the platform
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          label="Username"
          name="userName"
          fullWidth
          margin="normal"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={loading}
          autoComplete="off"
        />

        <TextField
          label="Password"
          name="password"
          type={showPassword ? "text" : "password"}
          fullWidth
          margin="normal"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          autoComplete="current-password"
          slotProps={{
            input: {
              endAdornment: (
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={() => setShowPassword(!showPassword)}
                  onMouseDown={(e) => e.preventDefault()}
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              )
            }
          }}
        />

        <Button
          variant="contained"
          color="primary"
          fullWidth
          onClick={handleLogin}
          disabled={loading || !username || !password}
          sx={{ mt: 3 }}
        >
          {loading ? "Logging in..." : "Log In"}
        </Button>

         <Typography variant="body2" align="center" sx={{ mt: 2, color: '#666' }}>
          Don't have an account?{' '}
            <Link onClick={props.onSwitchToRegister} sx={{ cursor: "pointer" }}>Register</Link>
        </Typography>
      </Paper>
    </Box>
  )
};

export default Login;
