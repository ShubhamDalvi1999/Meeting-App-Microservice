declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_AUTH_API_URL: string;
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: string;
  }
}

declare module '@react-oauth/google' {
  export interface GoogleLoginResponse {
    credential: string;
  }

  export interface GoogleLoginProps {
    onSuccess: (response: GoogleLoginResponse) => void;
    onError: () => void;
  }

  export const GoogleLogin: React.FC<GoogleLoginProps>;
  export const GoogleOAuthProvider: React.FC<{
    clientId: string;
    children: React.ReactNode;
  }>;
} 