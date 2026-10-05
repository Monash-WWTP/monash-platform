import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import "./index.css";
import LandingPage from "./pages/public/LandingPage";
import DownloadPage from "./pages/public/DownloadPage";
import ResearchPage from "./pages/public/ResearchPage";
import ResearchArticlePage from "./pages/public/ResearchArticlePage";
import ResearchReferencesPage from "./pages/public/ResearchReferencesPage";
import AccountPage from "./pages/public/AccountPage";
import NotFoundPage from "./pages/public/NotFoundPage";
import PublicLayout from "./pages/public/PublicLayout";

import LegacyPlantRedirect from "./pages/LegacyPlantRedirect";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/download", element: <DownloadPage /> },
      { path: "/research", element: <ResearchPage /> },
      { path: "/research/references", element: <ResearchReferencesPage /> },
      { path: "/research/:slug", element: <ResearchArticlePage /> },
      { path: "/login", element: <AccountPage /> },
      { path: "/register", element: <AccountPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    path: "/dashboard",
    lazy: async () => ({
      Component: (await import("./pages/MapPage")).default,
    }),
  },
  {
    path: "/dashboard/plants/:plantId",
    lazy: async () => ({
      Component: (await import("./pages/WorkspacePage")).default,
    }),
  },
  { path: "/dashboard/moderation", lazy: async () => ({ Component: (await import("./pages/ModerationPage")).default }) },
  { path: "/plants/:plantId", element: <LegacyPlantRedirect /> },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
