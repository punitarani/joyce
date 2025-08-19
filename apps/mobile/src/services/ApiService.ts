import { env } from '@/env';
import type { TokenRequest, TokenResponse } from '@/types';

// biome-ignore lint/complexity/noStaticOnlyClass: it's okay
export class ApiService {
  static async getToken(request: TokenRequest): Promise<TokenResponse> {
    try {
      const response = await fetch(`${env.EXPO_PUBLIC_API_URL}/api/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TokenResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get token:', error);
      throw new Error('Failed to get LiveKit token');
    }
  }

  static async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${env.EXPO_PUBLIC_API_URL}/api/health`);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}
