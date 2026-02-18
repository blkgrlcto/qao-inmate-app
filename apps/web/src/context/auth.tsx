"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { User } from "@/lib/api";
import * as api from "@/lib/api";

type AuthState = {
  token: string | null;
  user: User | null;
  loading: boolean;
};

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  setToken: (token: string | null) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "auth_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const setToken = useCallback((t: string | null) => {
    setTokenState(t);
    if (t) {
      document.cookie = `${TOKEN_KEY}=${t}; path=/; max-age=604800`; // 7 days
    } else {
      document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`;
    }
  }, []);

  useEffect(() => {
    const stored = document.cookie
      .split("; ")
      .find((c) => c.startsWith(`${TOKEN_KEY}=`))
      ?.split("=")[1];
    if (stored) {
      setTokenState(stored);
      api
        .me(stored)
        .then(setUser)
        .catch(() => setToken(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [setToken]);

  const login = useCallback(
    async (email: string, password: string): Promise<User> => {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      const u = await api.me(access_token);
      setUser(u);
      return u;
    },
    [setToken]
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, [setToken]);

  return (
    <AuthContext.Provider
      value={{ token, user, loading, login, logout, setToken }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
