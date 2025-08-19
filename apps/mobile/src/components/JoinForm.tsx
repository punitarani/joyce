import type React from 'react';
import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { ApiService } from '@/services/ApiService';

interface JoinFormProps {
  onJoin: (
    token: string,
    url: string,
    roomName: string,
    participantName: string
  ) => void;
}

export const JoinForm: React.FC<JoinFormProps> = ({ onJoin }) => {
  const [roomName, setRoomName] = useState('');
  const [participantName, setParticipantName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleJoin = async () => {
    if (!roomName.trim() || !participantName.trim()) {
      Alert.alert('Error', 'Please enter both room name and your name');
      return;
    }

    setIsLoading(true);

    try {
      const tokenResponse = await ApiService.getToken({
        roomName: roomName.trim(),
        participantName: participantName.trim(),
      });

      onJoin(
        tokenResponse.token,
        tokenResponse.url,
        roomName.trim(),
        participantName.trim()
      );
    } catch (error) {
      Alert.alert(
        'Connection Error',
        'Failed to connect to the server. Please try again.'
      );
      console.error('Join error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkServerHealth = async () => {
    setIsLoading(true);
    try {
      const isHealthy = await ApiService.checkHealth();
      Alert.alert(
        'Server Status',
        isHealthy
          ? 'Server is running and healthy!'
          : 'Server is not responding'
      );
    } catch (_error) {
      Alert.alert('Error', 'Failed to check server status');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Joyce Voice</Text>
      <Text style={styles.subtitle}>Real-time Audio Communication</Text>

      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Room Name"
          value={roomName}
          onChangeText={setRoomName}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <TextInput
          style={styles.input}
          placeholder="Your Name"
          value={participantName}
          onChangeText={setParticipantName}
          autoCapitalize="words"
          autoCorrect={false}
        />

        <TouchableOpacity
          style={[styles.button, styles.joinButton]}
          onPress={handleJoin}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>Join Room</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.healthButton]}
          onPress={checkServerHealth}
          disabled={isLoading}
        >
          <Text style={[styles.buttonText, { color: '#2196F3' }]}>
            Check Server Status
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
    color: '#2196F3',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 40,
    color: '#666',
  },
  form: {
    gap: 15,
  },
  input: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 8,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  button: {
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  joinButton: {
    backgroundColor: '#2196F3',
  },
  healthButton: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#2196F3',
  },
  buttonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
  },
});
