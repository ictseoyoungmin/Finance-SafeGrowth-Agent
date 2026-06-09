import { getApiBaseUrl } from "../compliance/api";
import type { AuthProfile, LoginResponse } from "./types";

export async function login(id: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${getApiBaseUrl()}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, password }),
  });
  if (response.status === 401) {
    throw new Error("로그인 정보가 올바르지 않습니다.");
  }
  if (!response.ok) {
    throw new Error(`로그인 요청이 실패했습니다 (${response.status}).`);
  }
  return (await response.json()) as LoginResponse;
}

export async function fetchMe(token: string): Promise<AuthProfile> {
  const response = await fetch(`${getApiBaseUrl()}/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error("token invalid");
  }
  return (await response.json()) as AuthProfile;
}

export async function logout(token: string): Promise<void> {
  await fetch(`${getApiBaseUrl()}/v1/auth/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}
