/// <reference types="node" />
import React, { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import Layout from '@/components/layout/Layout';

interface Meeting {
  id: number;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  created_by: number;
  created_at: string;
  updated_at: string;
  ended_at: string | null;
}

declare global {
  namespace NodeJS {
    interface ProcessEnv {
      NEXT_PUBLIC_API_URL: string;
    }
  }
}

export default function Dashboard() {
  const router = useRouter();
  const { token } = useAuth();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [meetingId, setMeetingId] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) {
      fetchMeetings();
    }
  }, [token]);

  const fetchMeetings = async () => {
    setIsLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('API URL is not configured');
      }

      const response = await fetch(`${apiUrl}/api/meetings/list?active_only=true`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch meetings');
      }

      const data = await response.json();
      setMeetings(data);
    } catch (err) {
      console.error('Error fetching meetings:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch meetings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateMeeting = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    
    try {
      // Enhanced client-side validation
      const trimmedTitle = title.trim();
      const trimmedDesc = description.trim();
      
      if (!trimmedTitle) {
        setError('Meeting title is required');
        return;
      }

      if (trimmedTitle.length > 200) {
        setError('Meeting title cannot exceed 200 characters');
        return;
      }

      if (trimmedDesc.length > 2000) {
        setError('Meeting description cannot exceed 2000 characters');
        return;
      }

      if (!startTime || !endTime) {
        setError('Start time and end time are required');
        return;
      }

      const startDate = new Date(startTime);
      const endDate = new Date(endTime);
      const now = new Date();

      if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
        setError('Invalid date format');
        return;
      }

      if (startDate < now) {
        setError('Meeting cannot start in the past');
        return;
      }

      if (startDate >= endDate) {
        setError('Start time must be before end time');
        return;
      }

      const duration = (endDate.getTime() - startDate.getTime()) / 1000; // in seconds
      if (duration < 300) { // 5 minutes
        setError('Meeting must be at least 5 minutes long');
        return;
      }

      if (duration > 86400) { // 24 hours
        setError('Meeting cannot be longer than 24 hours');
        return;
      }

      const oneYearFromNow = new Date();
      oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1);
      if (startDate > oneYearFromNow) {
        setError('Cannot schedule meetings more than 1 year in advance');
        return;
      }

      setIsCreating(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('API URL is not configured');
      }

      const response = await fetch(`${apiUrl}/api/meetings/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          title: trimmedTitle,
          description: trimmedDesc,
          start_time: startDate.toISOString(),
          end_time: endDate.toISOString()
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to create meeting');
      }

      // Update meetings list and reset form
      setMeetings((prevMeetings: Meeting[]) => [...prevMeetings, data]);
      setTitle('');
      setDescription('');
      setStartTime('');
      setEndTime('');
      setError('');
      
      // Show success message or redirect
      router.push(`/meeting/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create meeting');
    } finally {
      setIsCreating(false);
    }
  };

  const handleJoinMeeting = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    try {
      // Validate meeting ID
      const meetingIdNum = parseInt(meetingId);
      if (isNaN(meetingIdNum) || meetingIdNum <= 0) {
        setError('Please enter a valid meeting ID');
        return;
      }

      setIsJoining(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('API URL is not configured');
      }

      const response = await fetch(`${apiUrl}/api/meetings/join/${meetingIdNum}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle specific error cases
        if (data.starts_in_minutes) {
          setError(`Meeting starts in ${data.starts_in_minutes} minutes`);
        } else {
          throw new Error(data.error || 'Failed to join meeting');
        }
        return;
      }

      // Check if meeting is about to end
      if (data.time_remaining_minutes < 5) {
        setError('Warning: Meeting will end in less than 5 minutes');
        // Continue anyway after warning
      }

      router.push(`/meeting/${meetingIdNum}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join meeting');
    } finally {
      setIsJoining(false);
    }
  };

  const dashboardContent = (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Create Meeting */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Create New Meeting</h2>
          <form onSubmit={handleCreateMeeting}>
            <div className="mb-4">
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                Meeting Title
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>
            <div className="mb-4">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                rows={3}
              />
            </div>
            <div className="mb-4">
              <label htmlFor="startTime" className="block text-sm font-medium text-gray-700">
                Start Time
              </label>
              <input
                type="datetime-local"
                id="startTime"
                value={startTime}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setStartTime(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>
            <div className="mb-4">
              <label htmlFor="endTime" className="block text-sm font-medium text-gray-700">
                End Time
              </label>
              <input
                type="datetime-local"
                id="endTime"
                value={endTime}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setEndTime(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isCreating}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isCreating ? 'Creating...' : 'Create Meeting'}
            </button>
          </form>
        </div>

        {/* Join Meeting */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Join Meeting</h2>
          <form onSubmit={handleJoinMeeting}>
            <div className="mb-4">
              <label htmlFor="meetingId" className="block text-sm font-medium text-gray-700">
                Meeting ID
              </label>
              <input
                type="number"
                id="meetingId"
                value={meetingId}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setMeetingId(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isJoining}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              {isJoining ? 'Joining...' : 'Join Meeting'}
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="mt-6 bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded relative">
          {error}
        </div>
      )}

      {/* Recent Meetings */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-4">Recent Meetings</h2>
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          {isLoading ? (
            <div className="px-4 py-4 sm:px-6 text-center text-gray-500">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2">Loading meetings...</p>
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {meetings.map((meeting: Meeting) => (
                <li key={meeting.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-blue-600 truncate">
                          {meeting.title}
                        </p>
                        <p className="mt-1 text-sm text-gray-500">
                          {new Date(meeting.start_time).toLocaleString()} - {new Date(meeting.end_time).toLocaleString()}
                        </p>
                        {meeting.description && (
                          <p className="mt-1 text-sm text-gray-500 truncate">
                            {meeting.description}
                          </p>
                        )}
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <button
                          onClick={() => router.push(`/meeting/${meeting.id}`)}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                          Join
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
              {meetings.length === 0 && (
                <li>
                  <div className="px-4 py-4 sm:px-6 text-center text-gray-500">
                    No recent meetings
                  </div>
                </li>
              )}
            </ul>
          )}
        </div>
      </div>
    </div>
  );

  return <Layout>{dashboardContent}</Layout>;
} 