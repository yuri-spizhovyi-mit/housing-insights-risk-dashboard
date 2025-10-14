import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { FilterProvider } from "./context/FilterContext.tsx";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { LenisProvider } from "./context/LenisContext.tsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
    },
  },
});

const darkTheme = createTheme({
  components: {
    MuiSkeleton: {
      styleOverrides: {
        root: {
          backgroundColor: "var(--bg-skeleton-base)",
          "&::after": {
            background: "var(--bg-skeleton-highlight)",
          },
        },
      },
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <ReactQueryDevtools initialIsOpen={false} />
    <LenisProvider>
      <ThemeProvider theme={darkTheme}>
        <FilterProvider>
          <StrictMode>
            <App />
          </StrictMode>
        </FilterProvider>
      </ThemeProvider>
    </LenisProvider>
  </QueryClientProvider>
);
