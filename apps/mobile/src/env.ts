import { createEnv } from '@t3-oss/env-core';
import { z } from 'zod';

// Import environment variables from the project root .env file via react-native-dotenv
// @ts-expect-error - react-native-dotenv doesn't have types
import { EXPO_PUBLIC_API_URL } from '@env';

export const env = createEnv({
  // Server-side environment variables (none for React Native)
  server: {},

  // Client-side environment variables
  client: {
    // API Configuration
    EXPO_PUBLIC_API_URL: z
      .string()
      .url()
      .default('http://localhost:3000')
      .describe('API server URL'),
  },

  // Client prefix for public environment variables
  clientPrefix: 'EXPO_PUBLIC_',

  // Environment variables available in runtime
  runtimeEnv: {
    EXPO_PUBLIC_API_URL: EXPO_PUBLIC_API_URL || 'http://localhost:3000',
  },

  // Skip validation during build (for CI/CD)
  skipValidation: !!process.env.SKIP_ENV_VALIDATION,

  // Error messages
  emptyStringAsUndefined: true,
});
