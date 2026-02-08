import React from 'react';
import {
  Box,
  Button,
} from '@mui/material';

interface LoggedInActionsProps {
  onLogout: () => void;
}

const LoggedInActions: React.FC<LoggedInActionsProps> = ({ onLogout }) => {
  return (
    <>
      <Box sx={{ flexGrow: 1 }} />
      <Box sx={{ p: 2 }}>
        <Button
          variant="outlined"
          fullWidth
          onClick={onLogout}
          sx={{ textTransform: 'none' }}
        >
          Logout
        </Button>
      </Box>
    </>
  );
};

export default LoggedInActions;
