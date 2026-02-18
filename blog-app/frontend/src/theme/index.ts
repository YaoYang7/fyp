import { createTheme, type PaletteMode } from "@mui/material/styles";

export const getTheme = (mode: PaletteMode) =>
  createTheme({
    palette: {
      mode,

      primary: {
        main: "#1976d2",
        light: "#63a4ff",
        dark: "#004ba0",
        contrastText: "#ffffff",
      },

      secondary: {
        main: mode === "light" ? "#ffffff" : "#1e1e1e",
      },

      background: {
        default: mode === "light" ? "#f5f9ff" : "#121212",
        paper: mode === "light" ? "#ffffff" : "#1e1e1e",
      },

      text: {
        primary: mode === "light" ? "#0d1b2a" : "#e0e0e0",
        secondary: mode === "light" ? "#415a77" : "#a0aab4",
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
            backgroundColor: mode === "light" ? "#1976d2" : "#1a1a2e",
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: mode === "light" ? "#f5f5f5" : "#1e1e1e",
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            "&.Mui-selected": {
              backgroundColor:
                mode === "light"
                  ? "rgba(0, 0, 0, 0.12)"
                  : "rgba(255, 255, 255, 0.12)",
              "&:hover": {
                backgroundColor:
                  mode === "light"
                    ? "rgba(0, 0, 0, 0.16)"
                    : "rgba(255, 255, 255, 0.16)",
              },
            },
            "&:hover": {
              backgroundColor:
                mode === "light"
                  ? "rgba(0, 0, 0, 0.06)"
                  : "rgba(255, 255, 255, 0.06)",
            },
          },
        },
      },
    },
  });

export default getTheme("light");
