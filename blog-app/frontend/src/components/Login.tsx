import { Typography, Box, TextField, Paper, Button, Link } from "@mui/material";
import { useState } from "react";
import IconButton from "@mui/material/IconButton";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";


interface LoginProps {
  onSwitchToRegister: () => void;
}

const Login: React.FC<LoginProps> = (props) => {
  const [showPassword, setShowPassword] = useState(false);

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

        <TextField
          label="Username"
          name="userName"
          fullWidth
          margin="normal"
        />

        <TextField
          label="Password"
          name="password"
          type={showPassword ? "text" : "password"}
          fullWidth
          margin="normal"
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
          onClick={() => {}}
          sx={{ mt: 3 }}
        >
          Log In
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
