"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { MotionConfig } from "framer-motion";
import { useState, type ReactNode } from "react";
import { Toaster } from "sonner";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
        {/* reducedMotion="user" makes every framer-motion animation in the app
            respect the OS-level prefers-reduced-motion setting automatically. */}
        <MotionConfig reducedMotion="user">
          {children}
          <Toaster richColors position="top-right" closeButton />
        </MotionConfig>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
