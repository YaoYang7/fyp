import { useState } from 'react';
import { Box, Button, TextField, Typography, Paper, Link, Alert, CircularProgress } from '@mui/material';
import IconButton from "@mui/material/IconButton";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import { userApi } from '../services/usersAPI';

interface FormData {
  tenantName: string;
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface RegisterProps {
  onSwitchToLogin: () => void;
}

export default function Register(props: RegisterProps) {
  const [formData, setFormData] = useState<FormData>({
    tenantName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string>('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<FormData> = {};

    if (!formData.tenantName.trim()) {
      newErrors.tenantName = 'Organization name is required';
    }

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (validate()) {
      setLoading(true);
      setApiError('');

      try {
        await userApi.register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          tenant_name: formData.tenantName
        });

        setIsSubmitted(true);
      } catch (error: any) {
        console.error('Registration error:', error);

        if (error.response?.data?.detail) {
          setApiError(error.response.data.detail);
        } else if (error.response?.status === 400) {
          setApiError('Username or email already exists. Please try another.');
        } else if (error.message) {
          setApiError(`Registration failed: ${error.message}`);
        } else {
          setApiError('Registration failed. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleSubmit();
    }
  };

  if (isSubmitted) {
    return (
      <Box 
        sx={{
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, maxWidth: '500px', width: '100%' }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Registration Successful!
            </Typography>
            <Typography variant="body2" sx={{ color: '#666', mb: 3 }}>
              Welcome, {formData.username}! Your account has been created successfully.
            </Typography>
            <Button
              variant="outlined"
              color="primary"
              onClick={props.onSwitchToLogin}
            >
              Go to Login
            </Button>
          </Box>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',}}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: '500px', width: '100%' }}>
        <Typography variant="h4" gutterBottom>Register</Typography>
        <Typography variant="body2" sx={{ color: '#666', mb: 3 }}>
          Create an account to get started
        </Typography>

        {apiError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {apiError}
          </Alert>
        )}

        <TextField
          label="Organization Name"
          name="tenantName"
          value={formData.tenantName}
          onChange={handleChange}
          fullWidth
          margin="normal"
          error={!!errors.tenantName}
          helperText={errors.tenantName}
          autoComplete="off"
        />

        <TextField
          label="Username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          fullWidth
          margin="normal"
          error={!!errors.username}
          helperText={errors.username}
          autoComplete="off"
        />

        <TextField
          label="Email Address"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          fullWidth
          margin="normal"
          error={!!errors.email}
          helperText={errors.email}
          autoComplete="off"
        />

        <TextField
          label="Password"
          name="password"
          type={showPassword ? "text" : "password"}
          value={formData.password}
          onChange={handleChange}
          fullWidth
          margin="normal"
          error={!!errors.password}
          helperText={errors.password}
          autoComplete="new-password"
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

        <TextField
          label="Confirm Password"
          name="confirmPassword"
          type={showConfirmPassword ? "text" : "password"}
          value={formData.confirmPassword}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          fullWidth
          margin="normal"
          error={!!errors.confirmPassword}
          helperText={errors.confirmPassword}
          autoComplete="new-password"
          slotProps={{
            input: {
              endAdornment: (
                <IconButton
                  aria-label="toggle password visibility"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  onMouseDown={(e) => e.preventDefault()}
                >
                  {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              )
            }
          }}
        />

        <Button
          variant="contained"
          color="primary"
          fullWidth
          onClick={handleSubmit}
          disabled={loading}
          sx={{ mt: 3 }}
        >
          {loading ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
              Registering...
            </>
          ) : (
            'Register'
          )}
        </Button>

        <Typography variant="body2" align="center" sx={{ mt: 2, color: '#666' }}>
          Already have an account?{' '}
          <Link onClick={props.onSwitchToLogin} sx={{ cursor: "pointer" }}>Sign in</Link>
        </Typography>
      </Paper>
    </Box>
  );
}