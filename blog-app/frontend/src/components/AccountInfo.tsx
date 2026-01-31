import React from 'react';
import { Box, Typography, Avatar } from '@mui/material';
import { Person as PersonIcon } from '@mui/icons-material';
import { useAppSelector } from '../store/hooks';

const AccountInfo: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);

  if (!user) return null;

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Avatar sx={{ width: 56, height: 56, mb: 1, bgcolor: 'primary.main' }}>
          <PersonIcon />
        </Avatar>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {user.username}
        </Typography>
      </Box>
    </Box>
  );
};

export default AccountInfo;
