// Legacy config file - now using t3-env
// This file is kept for backward compatibility and re-exports from env.ts
import { env } from '@/env';

export const config = env;
export default config;
