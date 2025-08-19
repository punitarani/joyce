export interface TokenResponse {
  token: string;
  url: string;
}

export interface TokenRequest {
  roomName: string;
  participantName: string;
}

export interface CallState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  roomName: string | null;
  participantName: string | null;
}
