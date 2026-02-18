import type { SxProps, Theme } from '@mui/material';

export const editorContainer: SxProps<Theme> = {
  border: 1,
  borderColor: 'divider',
  borderRadius: 1,
};

export const toolbar: SxProps<Theme> = {
  display: 'flex',
  flexWrap: 'wrap',
  p: 0.5,
  borderBottom: 1,
  borderColor: 'divider',
  bgcolor: 'action.hover',
};

export const toolbarDivider: SxProps<Theme> = {
  mx: 0.5,
};

export const editorArea: SxProps<Theme> = (theme: Theme) => ({
  p: 2,
  minHeight: 300,
  '& .ProseMirror': { outline: 'none', minHeight: 280 },
  '& .ProseMirror p': { margin: '0.5em 0' },
  '& .ProseMirror img': { maxWidth: '50%', height: 'auto', borderRadius: '4px' },
  '& .ProseMirror video': { maxWidth: '100%', borderRadius: '4px' },
  '& .ProseMirror h1, & .ProseMirror h2, & .ProseMirror h3': { margin: '0.75em 0 0.25em' },
  '& .ProseMirror blockquote': {
    borderLeft: `3px solid ${theme.palette.divider}`,
    paddingLeft: '1em',
    color: theme.palette.text.secondary,
  },
  '& .ProseMirror code': {
    background: theme.palette.action.hover,
    padding: '2px 4px',
    borderRadius: '3px',
  },
  '& .ProseMirror pre': {
    background: theme.palette.action.hover,
    padding: '1em',
    borderRadius: '4px',
    overflowX: 'auto',
  },
});
