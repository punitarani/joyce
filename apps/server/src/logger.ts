import { env } from '@/env';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: Error;
}

class Logger {
  private isDevelopment = env.NODE_ENV === 'development';

  private formatMessage(entry: LogEntry): string {
    const { timestamp, level, message, context, error } = entry;

    let logMessage = `[${timestamp}] ${level.toUpperCase()}: ${message}`;

    if (context && Object.keys(context).length > 0) {
      logMessage += ` | Context: ${JSON.stringify(context)}`;
    }

    if (error) {
      logMessage += ` | Error: ${error.message}`;
      if (this.isDevelopment && error.stack) {
        logMessage += `\nStack: ${error.stack}`;
      }
    }

    return logMessage;
  }

  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    error?: Error
  ): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      error,
    };

    const formattedMessage = this.formatMessage(entry);

    switch (level) {
      case 'debug':
        if (this.isDevelopment) {
          console.debug(formattedMessage);
        }
        break;
      case 'info':
        console.info(formattedMessage);
        break;
      case 'warn':
        console.warn(formattedMessage);
        break;
      case 'error':
        console.error(formattedMessage);
        break;
    }
  }

  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context);
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context);
  }

  warn(
    message: string,
    context?: Record<string, unknown>,
    error?: Error
  ): void {
    this.log('warn', message, context, error);
  }

  error(
    message: string,
    context?: Record<string, unknown>,
    error?: Error
  ): void {
    this.log('error', message, context, error);
  }

  // Specific methods for common use cases
  agentStarted(roomName: string): void {
    this.info('Voice agent started', { roomName });
  }

  agentError(error: Error, roomName?: string): void {
    this.error('Voice agent error', { roomName }, error);
  }

  webhookReceived(callSid: string, from: string): void {
    this.info('Webhook received', { callSid, from });
  }

  webhookError(error: Error, callSid?: string): void {
    this.error('Webhook error', { callSid }, error);
  }

  callInitiated(callSid: string, to: string): void {
    this.info('Call initiated', { callSid, to });
  }

  callError(error: Error, to?: string): void {
    this.error('Call error', { to }, error);
  }

  serverStarted(port: number): void {
    this.info('Server started', { port });
  }

  serverError(error: Error): void {
    this.error('Server error', {}, error);
  }
}

export const logger = new Logger();
export default logger;
