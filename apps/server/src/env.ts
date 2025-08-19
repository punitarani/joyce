import { createEnv } from '@t3-oss/env-core';
import { z } from 'zod';
import dotenv from 'dotenv';
import { join } from 'node:path';

// Load environment variables from project root .env file
dotenv.config({ path: join(import.meta.dirname, '../../../.env') });

export const env = createEnv({
  server: {
    // LiveKit Configuration
    LIVEKIT_URL: z.string().url().describe('LiveKit server URL'),
    LIVEKIT_API_KEY: z.string().min(1).describe('LiveKit API key'),
    LIVEKIT_API_SECRET: z.string().min(1).describe('LiveKit API secret'),

    // OpenAI Configuration
    OPENAI_API_KEY: z.string().min(1).describe('OpenAI API key'),

    // Server Configuration
    PORT: z.coerce
      .number()
      .int()
      .min(1)
      .max(65535)
      .default(3000)
      .describe('Server port'),
    NODE_ENV: z
      .enum(['development', 'production', 'test'])
      .default('development')
      .describe('Node environment'),
  },

  // Client-side environment variables (none for server)
  client: {},

  // Client prefix for public environment variables
  clientPrefix: 'PUBLIC_',

  // Environment variables available in runtime
  runtimeEnv: {
    LIVEKIT_URL: process.env.LIVEKIT_URL,
    LIVEKIT_API_KEY: process.env.LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET: process.env.LIVEKIT_API_SECRET,
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    PORT: process.env.PORT,
    NODE_ENV: process.env.NODE_ENV,
  },

  // Skip validation during build (for CI/CD)
  skipValidation: !!process.env.SKIP_ENV_VALIDATION,

  // Error messages
  emptyStringAsUndefined: true,
});
