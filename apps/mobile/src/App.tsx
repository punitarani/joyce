import type React from 'react';
import { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, Alert } from 'react-native';
import { LiveKitRoom, registerGlobals } from '@livekit/react-native';
import { JoinForm } from '@/components/JoinForm';
import { RoomView } from '@/components/RoomView';
import type { CallState } from '@/types';

// Register LiveKit globals
registerGlobals();

const App: React.FC = () => {
  const [_callState, setCallState] = useState<CallState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    roomName: null,
    participantName: null,
  });

  const [connectionInfo, setConnectionInfo] = useState<{
    token: string;
    url: string;
  } | null>(null);

  const handleJoin = (
    token: string,
    url: string,
    roomName: string,
    participantName: string
  ) => {
    setConnectionInfo({ token, url });
    setCallState({
      isConnected: false,
      isConnecting: true,
      error: null,
      roomName,
      participantName,
    });
  };

  const handleEndCall = () => {
    setConnectionInfo(null);
    setCallState({
      isConnected: false,
      isConnecting: false,
      error: null,
      roomName: null,
      participantName: null,
    });
  };

  const handleRoomConnect = () => {
    setCallState((prev) => ({
      ...prev,
      isConnected: true,
      isConnecting: false,
      error: null,
    }));
  };

  const handleRoomDisconnect = () => {
    setCallState((prev) => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  };

  const handleRoomError = (error: Error) => {
    console.error('Room error:', error);
    setCallState((prev) => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: error.message,
    }));

    Alert.alert('Connection Error', error.message, [
      { text: 'OK', onPress: handleEndCall },
    ]);
  };

  if (connectionInfo) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#2196F3" />
        <LiveKitRoom
          serverUrl={connectionInfo.url}
          token={connectionInfo.token}
          connectOptions={{
            autoSubscribe: true,
          }}
          roomOptions={{
            adaptiveStream: true,
            dynacast: true,
          }}
          onConnected={handleRoomConnect}
          onDisconnected={handleRoomDisconnect}
          onError={handleRoomError}
        >
          <RoomView onEndCall={handleEndCall} />
        </LiveKitRoom>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f5f5f5" />
      <JoinForm onJoin={handleJoin} />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});

export default App;
