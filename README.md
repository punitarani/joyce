# Joyce Voice - Turbo Repo with LiveKit Server & React Native

A Turbo repo setup with a LiveKit server and React Native mobile app for real-time audio communication.

## Setup

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Fill in your credentials in `.env`:
   - LiveKit: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
   - Server: `PORT`, `NODE_ENV`

3. Install dependencies:
   ```bash
   bun install
   ```

### Environment Variables

This project uses **t3-env** for type-safe environment variable management with a **centralized .env file** at the project root:

- **Server** (`apps/server/src/env.ts`): Loads from project root `.env` using dotenv
- **Mobile** (`apps/mobile/src/env.ts`): Loads from project root `.env` using react-native-dotenv

**Configuration:**
- Server variables: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`, `PORT`, `NODE_ENV`
- Mobile variables: `EXPO_PUBLIC_API_URL` (prefixed for React Native)

All environment variables are type-safe and validated at runtime with helpful error messages.

## Development

### Server

```bash
# Run the LiveKit voice agent (for AI voice conversations)
bun dev --filter=server
# OR
bun agent --filter=server

# Run the HTTP server (for mobile token generation)
bun server --filter=server

# Or use turbo commands
turbo dev    # Runs the LiveKit voice agent (primary development)
turbo agent  # Runs the LiveKit voice agent (same as dev)
turbo server # Runs the HTTP API server
```

### Mobile

```bash
# Start React Native metro bundler
bun mobile:start

# Run on Android
bun mobile:android

# Run on iOS
bun mobile:ios

# Or use turbo commands
turbo start --filter=mobile
turbo android --filter=mobile
turbo ios --filter=mobile
```

### Code Quality

```bash
# Format code across all apps
turbo format

# Lint code across all apps
turbo lint
```

## Architecture

- **Server App**: LiveKit voice agent + HTTP API for token generation
  - **LiveKit Voice Agent**: Real-time voice conversations using OpenAI Realtime API
  - **HTTP API**: Generates LiveKit tokens for mobile clients
  - **OpenAI Realtime**: Native voice-to-voice AI conversations (no STT/TTS needed)

- **Mobile App**: React Native with LiveKit real-time audio
  - **No Auth**: Simple join with room name and participant name
  - **Real-time Audio**: LiveKit WebRTC for high-quality voice communication
  - **Cross-platform**: Works on both iOS and Android

- **Biome.js**: Handles formatting and linting with `turbo format` and `turbo lint`

## Structure

```
├── apps/
│   ├── server/          # LiveKit server + HTTP API
│   │   ├── src/
│   │   │   ├── index.ts    # Main LiveKit agent
│   │   │   ├── server.ts   # HTTP API for token generation
│   │   │   ├── config.ts   # Environment configuration
│   │   │   └── logger.ts   # Structured logging
│   │   └── package.json
│   └── mobile/          # React Native mobile app
│       ├── src/
│       │   ├── App.tsx         # Main app component
│       │   ├── components/     # UI components
│       │   ├── services/       # API services
│       │   └── types/          # TypeScript types
│       └── package.json
├── packages/            # Shared packages (empty for now)
├── biome.json          # Biome configuration
├── turbo.json          # Turbo configuration
└── package.json        # Root package.json
```

## Usage

1. **Start the voice agent**: `turbo dev` - This runs the LiveKit voice agent continuously for AI conversations  
2. **Start the token server**: `turbo server` - This runs the HTTP API on port 3000
3. **Start the mobile app**: `turbo start --filter=mobile` then `turbo android --filter=mobile`
4. **Join a room**: Enter a room name and your name in the mobile app
5. **Talk to Joyce**: The AI voice assistant will respond in real-time using OpenAI Realtime API

## API Endpoints

- `POST /api/token` - Generate LiveKit token for room access
- `GET /api/health` - Health check endpoint