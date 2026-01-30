import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "light",

    primary: {
      main: "#1976d2", // MUI default blue
      light: "#63a4ff",
      dark: "#004ba0",
      contrastText: "#ffffff",
    },

    secondary: {
      main: "#ffffff",
    },

    background: {
      default: "#f5f9ff", // soft blue-white background
      paper: "#ffffff",
    },

    text: {
      primary: "#0d1b2a",
      secondary: "#415a77",
    },
  },

  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: "none",
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#1976d2",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: "#f5f5f5",
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          "&.Mui-selected": {
            backgroundColor: "#d0d0d0",
            "&:hover": {
              backgroundColor: "#c0c0c0",
            },
          },
          "&:hover": {
            backgroundColor: "#e8e8e8",
          },
        },
      },
    },
  },
});

export default theme;
