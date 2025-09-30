import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { FilterProvider } from "./context/FilterContext.tsx";
import { createTheme, ThemeProvider } from "@mui/material/styles";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0,
    },
  },
});

const theme = createTheme();

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <ReactQueryDevtools initialIsOpen={false} />

    <ThemeProvider theme={theme}>
      <FilterProvider>
        <StrictMode>
          <App />
        </StrictMode>
      </FilterProvider>
    </ThemeProvider>
  </QueryClientProvider>
);
