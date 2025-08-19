import {
  type JobContext,
  WorkerOptions,
  cli,
  defineAgent,
  multimodal,
  llm,
} from '@livekit/agents';
import * as openai from '@livekit/agents-plugin-openai';
import { fileURLToPath } from 'node:url';
import { env } from '@/env';
import { logger } from '@/logger';

export default defineAgent({
  entry: async (ctx: JobContext) => {
    try {
      await ctx.connect();
      logger.info('Agent connected to room', { roomName: ctx.room.name });

      console.log('waiting for participant');
      const participant = await ctx.waitForParticipant();
      logger.info('Participant joined', {
        participantIdentity: participant.identity,
        roomName: ctx.room.name,
      });

      // Create OpenAI Realtime model for voice-to-voice
      const model = new openai.realtime.RealtimeModel({
        instructions: `You are Joyce, a helpful voice assistant. Keep your responses natural, conversational, and concise. 
        You are having a voice conversation, so speak naturally as if talking to a friend. 
        Be warm, friendly, and engaging in your responses.`,
        voice: 'alloy', // Use alloy voice
      });

      // Create the multimodal agent for voice interaction
      const agent = new multimodal.MultimodalAgent({
        model,
      });

      logger.info('Starting voice agent session', {
        participantIdentity: participant.identity,
      });

      // Start the agent session
      const session = await agent
        .start(ctx.room, participant)
        .then((session) => session as openai.realtime.RealtimeSession);

      // Send initial greeting
      session.conversation.item.create(
        llm.ChatMessage.create({
          role: llm.ChatRole.USER,
          text: 'Say "Hello! I\'m Joyce, your voice assistant. How can I help you today?"',
        })
      );

      // Generate the initial response
      session.response.create();

      logger.info('Voice agent session started successfully', {
        participantIdentity: participant.identity,
        roomName: ctx.room.name,
      });

      // Handle session events
      session.on('response.done', (response) => {
        logger.debug('Response completed', {
          responseId: response.id,
          participantIdentity: participant.identity,
        });
      });

      session.on('error', (error) => {
        logger.error(
          'Session error',
          {
            participantIdentity: participant.identity,
          },
          error
        );
      });

      // Keep the session alive
      await new Promise((resolve, reject) => {
        ctx.room.on('disconnected', resolve);
        session.on('error', reject);
      });
    } catch (error) {
      logger.error('Agent error', { roomName: ctx.room?.name }, error as Error);
      throw error;
    }
  },
});

// Handle CLI arguments and run the agent
if (import.meta.main) {
  console.log('Starting LiveKit agent worker...');
  console.log('Environment check:');
  console.log('- LIVEKIT_URL:', env.LIVEKIT_URL ? '✓ Set' : '✗ Missing');
  console.log(
    '- LIVEKIT_API_KEY:',
    env.LIVEKIT_API_KEY ? '✓ Set' : '✗ Missing'
  );
  console.log(
    '- LIVEKIT_API_SECRET:',
    env.LIVEKIT_API_SECRET ? '✓ Set' : '✗ Missing'
  );
  console.log('- OPENAI_API_KEY:', env.OPENAI_API_KEY ? '✓ Set' : '✗ Missing');

  // Set required environment variables for LiveKit
  process.env.OPENAI_API_KEY = env.OPENAI_API_KEY;
  process.env.LIVEKIT_URL = env.LIVEKIT_URL;
  process.env.LIVEKIT_API_KEY = env.LIVEKIT_API_KEY;
  process.env.LIVEKIT_API_SECRET = env.LIVEKIT_API_SECRET;

  console.log('Starting worker with CLI...');
  // Use WorkerOptions to properly configure the agent
  cli.runApp(
    new WorkerOptions({
      agent: fileURLToPath(import.meta.url),
    })
  );
}
