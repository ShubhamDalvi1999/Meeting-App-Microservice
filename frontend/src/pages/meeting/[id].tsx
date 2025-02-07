import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/layout/Layout';
import VideoConference from '@/components/meeting/VideoConference';
import Whiteboard from '@/components/meeting/Whiteboard';
import Chat from '@/components/meeting/Chat';

interface Meeting {
  id: number;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export default function MeetingRoom() {
  const router = useRouter();
  const { id } = router.query;
  const { token, user } = useAuth();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [activeTab, setActiveTab] = useState<'whiteboard' | 'chat'>('chat');
  const [error, setError] = useState('');

  useEffect(() => {
    if (id && token) {
      fetchMeetingDetails();
    }
  }, [id, token]);

  const fetchMeetingDetails = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/meetings/join/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Meeting not found or inactive');
      }

      const data = await response.json();
      setMeeting(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join meeting');
      router.push('/dashboard');
    }
  };

  const handleEndMeeting = async () => {
    if (!meeting || meeting.created_by !== user?.id) return;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/meetings/end/${id}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to end meeting');
      }

      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end meeting');
    }
  };

  const MeetingInfo = ({ meeting }: { meeting: Meeting }) => (
    <div className="bg-white border-b px-4 py-2 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold">{meeting.title}</h1>
        <p className="text-sm text-gray-500">ID: {meeting.id}</p>
        <p className="text-sm text-gray-500">
          {new Date(meeting.start_time).toLocaleString()} - {new Date(meeting.end_time).toLocaleString()}
        </p>
      </div>
      <div className="flex items-center space-x-4">
        {meeting.created_by === user?.id && (
          <button
            onClick={handleEndMeeting}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            End Meeting
          </button>
        )}
        <button
          onClick={() => router.push('/dashboard')}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
        >
          Leave
        </button>
      </div>
    </div>
  );

  if (!meeting) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <MeetingInfo meeting={meeting} />

        {/* Main Content */}
        <div className="flex-grow grid grid-cols-12 gap-4 p-4">
          {/* Video Conference */}
          <div className="col-span-8 bg-gray-900 rounded-lg overflow-hidden">
            <VideoConference roomId={meeting.id.toString()} />
          </div>

          {/* Sidebar */}
          <div className="col-span-4 flex flex-col bg-white rounded-lg overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b">
              <button
                onClick={() => setActiveTab('whiteboard')}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  activeTab === 'whiteboard'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Whiteboard
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  activeTab === 'chat'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Chat
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-grow">
              {activeTab === 'whiteboard' ? <Whiteboard /> : <Chat roomId={meeting.id.toString()} />}
            </div>
          </div>
        </div>

        {error && (
          <div className="fixed bottom-4 right-4 bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
      </div>
    </Layout>
  );
} 