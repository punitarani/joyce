import express from 'express';
import { AccessToken } from 'livekit-server-sdk';
import { env } from '@/env';
import { logger } from '@/logger';

const app = express();

app.use(express.json());

interface TokenRequest {
  roomName: string;
  participantName: string;
}

interface TokenResponse {
  token: string;
  url: string;
}

app.post('/api/token', async (req, res) => {
  try {
    const { roomName, participantName }: TokenRequest = req.body;

    if (!roomName || !participantName) {
      return res.status(400).json({
        error: 'roomName and participantName are required',
      });
    }

    if (roomName.length > 64 || participantName.length > 64) {
      return res.status(400).json({
        error: 'roomName and participantName must be less than 64 characters',
      });
    }

    const sanitizedRoomName = roomName.replace(/[^a-zA-Z0-9_-]/g, '_');
    const sanitizedParticipantName = participantName.replace(
      /[^a-zA-Z0-9_-]/g,
      '_'
    );

    const token = new AccessToken(env.LIVEKIT_API_KEY, env.LIVEKIT_API_SECRET, {
      identity: sanitizedParticipantName,
      name: sanitizedParticipantName,
      ttl: 3600, // 1 hour
    });

    token.addGrant({
      room: sanitizedRoomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: false,
      canUpdateOwnMetadata: false,
    });

    const jwt = await token.toJwt();

    logger.info('Token generated', {
      roomName: sanitizedRoomName,
      participantName: sanitizedParticipantName,
    });

    const response: TokenResponse = {
      token: jwt,
      url: env.LIVEKIT_URL,
    };

    res.json(response);
  } catch (error) {
    logger.error('Token generation failed', {}, error as Error);
    res.status(500).json({
      error: 'Internal server error',
    });
  }
});

app.get('/api/health', (_req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'joyce-server',
  });
});

app.listen(env.PORT, () => {
  logger.serverStarted(env.PORT);
  logger.info('API endpoints available', {
    tokenEndpoint: `http://localhost:${env.PORT}/api/token`,
    healthEndpoint: `http://localhost:${env.PORT}/api/health`,
  });
});

export default app;
