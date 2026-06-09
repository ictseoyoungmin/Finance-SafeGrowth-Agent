export type UserRole = "tester" | "admin";

export interface AuthProfile {
  id: string;
  role: UserRole;
  display_name: string;
  title: string;
  team: string;
}

export interface LoginResponse {
  token: string;
  profile: AuthProfile;
}
