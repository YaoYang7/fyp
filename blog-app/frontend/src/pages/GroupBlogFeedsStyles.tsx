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

export const emptyMessage: SxProps<Theme> = {
  textAlign: 'center',
  py: 4,
};

export const listItemBorder: SxProps<Theme> = {
  borderBottom: 1,
  borderColor: 'divider',
  px: 0,
};

export const listItemLast: SxProps<Theme> = {
  px: 0,
};

export const avatar: SxProps<Theme> = {
  bgcolor: 'primary.main',
};

export const postTitleRow: SxProps<Theme> = {
  display: 'flex',
  alignItems: 'center',
  gap: 1,
};

export const secondaryContent: SxProps<Theme> = {
  mt: 1,
};

export const summaryText: SxProps<Theme> = {
  mb: 1,
};

export const contentPreview: SxProps<Theme> = {
  fontSize: '0.875rem',
  color: 'text.secondary',
  '& img': { width: '10%', height: 'auto' },
  '& video': { display: 'none' },
};

export const metaRow: SxProps<Theme> = {
  display: 'flex',
  gap: 2,
  alignItems: 'center',
};

export const viewButton: SxProps<Theme> = {
  ml: 2,
  whiteSpace: 'nowrap',
};
