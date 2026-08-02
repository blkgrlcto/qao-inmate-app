"use client";

import { usePathname, useRouter } from "next/navigation";
import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { User } from "@/lib/api";
import * as api from "@/lib/api";

type AuthState = {
  user: User | null;
  loading: boolean;
};

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

// Pages that don't require a session — no redirect-to-login for these.
const PUBLIC_PATHS = ["/", "/login"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Without this, a page whose data-fetching effects gate on `user` (most
    // of them) just hangs on its loading state forever once session cookies
    // are missing/expired/revoked — there's no other global auth guard.
    if (!loading && !user && pathname && !PUBLIC_PATHS.includes(pathname)) {
      router.replace("/login");
    }
  }, [loading, user, pathname, router]);

  const login = useCallback(async (email: string, password: string): Promise<User> => {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error((err as { detail?: string }).detail || "Login failed");
    }
    const { user: u } = (await res.json()) as { user: User };
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(async () => {
    await fetch("/api/logout", { method: "POST" });
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
