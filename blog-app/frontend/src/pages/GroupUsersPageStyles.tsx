import type { SxProps, Theme } from '@mui/material';

export const loadingContainer: SxProps<Theme> = {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '60vh',
};

export const pageContainer: SxProps<Theme> = {
  p: 3,
};

export const errorAlert: SxProps<Theme> = {
  mb: 3,
};

export const paper: SxProps<Theme> = {
  p: 3,
};

export const headerRow: SxProps<Theme> = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  mb: 1,
};

export const divider: SxProps<Theme> = {
  mb: 2,
};

export const dataGridWrapper: SxProps<Theme> = {
  width: '100%',
};

export const avatarCell: SxProps<Theme> = {
  display: 'flex',
  alignItems: 'center',
  gap: 1,
  height: '100%',
};

export const avatarSx = (isCurrentUser: boolean): SxProps<Theme> => ({
  width: 28,
  height: 28,
  fontSize: 13,
  bgcolor: isCurrentUser ? 'primary.main' : 'grey.400',
});

export const usernameSx = (isCurrentUser: boolean): SxProps<Theme> => ({
  fontWeight: isCurrentUser ? 700 : 400,
  color: isCurrentUser ? 'primary.main' : 'text.primary',
});
