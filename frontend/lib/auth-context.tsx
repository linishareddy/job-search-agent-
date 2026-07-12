"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth-storage";
import type { User } from "@/lib/types/auth";

interface AuthContextValue {
  user: User | null;
  /** True only while we're checking a token that's actually present — an
   * unauthenticated visitor never sits in a loading state. */
  isLoading: boolean;
  isAuthenticated: boolean;
  /** False only for the first tick before we've read localStorage — lets a
   * route guard tell "not logged in" apart from "haven't checked yet" so it
   * doesn't redirect a logged-in user during that first render. */
  checked: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  // localStorage isn't available during SSR/first paint, so token presence is
  // read in an effect rather than during render to avoid a hydration mismatch.
  const [hasToken, setHasToken] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    setHasToken(!!getToken());
    setChecked(true);
  }, []);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.me(),
    enabled: hasToken,
    retry: false,
  });

  function login(token: string) {
    setToken(token);
    setHasToken(true);
    queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
  }

  function logout() {
    clearToken();
    setHasToken(false);
    queryClient.clear();
  }

  const user = hasToken && !isError ? (data?.data ?? null) : null;

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading: hasToken && isLoading,
        isAuthenticated: hasToken && !isError,
        checked,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
