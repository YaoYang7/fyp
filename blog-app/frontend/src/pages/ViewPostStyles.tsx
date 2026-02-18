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

export const backButton: SxProps<Theme> = {
  mb: 2,
};

export const paper: SxProps<Theme> = {
  p: 4,
};

export const title: SxProps<Theme> = {
  mb: 1,
};

export const metaRow: SxProps<Theme> = {
  display: 'flex',
  alignItems: 'center',
  gap: 2,
  mb: 2,
};

export const metaIconGroup: SxProps<Theme> = {
  display: 'flex',
  alignItems: 'center',
  gap: 0.5,
};

export const metaIcon: SxProps<Theme> = {
  fontSize: 14,
  color: 'text.secondary',
};

export const summary: SxProps<Theme> = {
  mb: 2,
  fontStyle: 'italic',
};

export const divider: SxProps<Theme> = {
  mb: 3,
};

export const contentArea: SxProps<Theme> = {
  '& img': { width: '50%', height: 'auto' },
  '& video': { maxWidth: '100%' },
};
