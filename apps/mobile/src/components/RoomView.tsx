import { AudioSession, useParticipants, useRoom } from '@livekit/react-native';
import React from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { CallControls } from '@/components/CallControls';

interface RoomViewProps {
  onEndCall: () => void;
}

export const RoomView: React.FC<RoomViewProps> = ({ onEndCall }) => {
  const { room, isConnected } = useRoom();
  const participants = useParticipants();

  React.useEffect(() => {
    // Configure audio session for voice calls
    AudioSession.configureAudio({
      android: {
        preferredOutputList: ['speaker'],
        audioTypeOptions: 'communication',
      },
      ios: {
        categoryOptions: ['defaultToSpeaker', 'allowBluetooth'],
        category: 'playAndRecord',
        mode: 'voiceChat',
      },
    });

    return () => {
      AudioSession.stopAudio();
    };
  }, []);

  if (!isConnected || !room) {
    return (
      <View style={styles.container}>
        <Text style={styles.statusText}>Connecting...</Text>
      </View>
    );
  }

  const renderParticipant = ({
    item: participant,
  }: {
    item: LocalParticipant | RemoteParticipant;
  }) => {
    const isLocal = participant.isLocal;
    const hasAudio = participant.audioTrackPublications.size > 0;
    const audioTrack = participant.audioTrackPublications.values().next()
      .value?.track;
    const isMuted = audioTrack?.muted ?? true;

    return (
      <View style={styles.participantCard}>
        <Text style={styles.participantName}>
          {participant.name || participant.identity} {isLocal ? '(You)' : ''}
        </Text>
        <Text style={styles.participantStatus}>
          {hasAudio ? (isMuted ? '🔇 Muted' : '🎤 Speaking') : '❌ No Audio'}
        </Text>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.roomTitle}>Room: {room.name}</Text>
        <Text style={styles.participantCount}>
          {participants.length} participant
          {participants.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <FlatList
        data={participants}
        renderItem={renderParticipant}
        keyExtractor={(participant) => participant.identity}
        style={styles.participantsList}
        contentContainerStyle={styles.participantsContainer}
      />

      <CallControls onEndCall={onEndCall} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#2196F3',
    alignItems: 'center',
  },
  roomTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  participantCount: {
    fontSize: 16,
    color: 'white',
    opacity: 0.8,
  },
  participantsList: {
    flex: 1,
  },
  participantsContainer: {
    padding: 20,
  },
  participantCard: {
    backgroundColor: 'white',
    padding: 15,
    marginBottom: 10,
    borderRadius: 8,
    elevation: 2,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  participantName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  participantStatus: {
    fontSize: 14,
    color: '#666',
  },
  statusText: {
    fontSize: 18,
    textAlign: 'center',
    marginTop: 50,
    color: '#666',
  },
});
