import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { setAuthToken } from "../compliance/api";
import { fetchMe, login as loginRequest, logout as logoutRequest } from "./api";
import type { AuthProfile } from "./types";

interface AuthContextValue {
  status: "loading" | "authenticated" | "unauthenticated";
  profile: AuthProfile | null;
  login: (id: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const STORAGE_KEY = "compliance.auth.v1";

const AuthContext = createContext<AuthContextValue | null>(null);

interface PersistedAuth {
  token: string;
  profile: AuthProfile;
}

function loadPersisted(): PersistedAuth | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<PersistedAuth>;
    if (!parsed?.token || !parsed.profile) return null;
    return { token: parsed.token, profile: parsed.profile };
  } catch {
    return null;
  }
}

function persist(value: PersistedAuth | null) {
  if (value) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [profile, setProfile] = useState<AuthProfile | null>(null);

  // Restore from localStorage and verify token with /me. If the token is
  // expired or invalid we drop it and fall back to the login screen.
  useEffect(() => {
    const persisted = loadPersisted();
    if (!persisted) {
      setStatus("unauthenticated");
      return;
    }
    setAuthToken(persisted.token);
    fetchMe(persisted.token)
      .then((freshProfile) => {
        setProfile(freshProfile);
        persist({ token: persisted.token, profile: freshProfile });
        setStatus("authenticated");
      })
      .catch(() => {
        setAuthToken(null);
        persist(null);
        setProfile(null);
        setStatus("unauthenticated");
      });
  }, []);

  const login = useCallback(async (id: string, password: string) => {
    const result = await loginRequest(id, password);
    setAuthToken(result.token);
    persist({ token: result.token, profile: result.profile });
    setProfile(result.profile);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    const persisted = loadPersisted();
    if (persisted?.token) {
      try {
        await logoutRequest(persisted.token);
      } catch {
        // ignore — local state is the source of truth post-logout
      }
    }
    setAuthToken(null);
    persist(null);
    setProfile(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, profile, login, logout }),
    [status, profile, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
