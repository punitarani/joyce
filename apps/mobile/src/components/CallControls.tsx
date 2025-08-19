import type React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useRoom } from '@livekit/react-native';

interface CallControlsProps {
  onEndCall: () => void;
}

export const CallControls: React.FC<CallControlsProps> = ({ onEndCall }) => {
  const { localParticipant, isConnected } = useRoom();

  const toggleAudio = () => {
    if (localParticipant) {
      const audioTrack = localParticipant.audioTrackPublications.values().next()
        .value?.track;
      if (audioTrack) {
        audioTrack.muted = !audioTrack.muted;
      }
    }
  };

  const handleEndCall = () => {
    Alert.alert('End Call', 'Are you sure you want to end the call?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'End Call', style: 'destructive', onPress: onEndCall },
    ]);
  };

  if (!isConnected) {
    return null;
  }

  const audioTrack = localParticipant?.audioTrackPublications.values().next()
    .value?.track;
  const isMuted = audioTrack?.muted ?? false;

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={[
          styles.button,
          isMuted ? styles.mutedButton : styles.audioButton,
        ]}
        onPress={toggleAudio}
      >
        <Text style={styles.buttonText}>{isMuted ? '🔇' : '🎤'}</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.endCallButton]}
        onPress={handleEndCall}
      >
        <Text style={styles.buttonText}>📞</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 40,
    gap: 20,
  },
  button: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  audioButton: {
    backgroundColor: '#4CAF50',
  },
  mutedButton: {
    backgroundColor: '#f44336',
  },
  endCallButton: {
    backgroundColor: '#f44336',
  },
  buttonText: {
    fontSize: 24,
    color: 'white',
  },
});
