import { useState, useEffect } from 'react';
import { Calendar, Clock, ExternalLink, User, Loader, Video } from 'lucide-react';

interface CalBooking {
  id: number;
  title: string;
  startTime: string;
  endTime: string;
  attendees: Array<{ email: string; name: string; timeZone: string }>;
  status: string;
  description?: string;
}

export default function CalendarWidget() {
  const [bookings, setBookings] = useState<CalBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [calStatus, setCalStatus] = useState<any>(null);

  useEffect(() => {
    fetchCalStatus();
    fetchUpcomingBookings();
  }, []);

  async function fetchCalStatus() {
    try {
      const response = await fetch('/cal/status');
      if (response.ok) {
        const data = await response.json();
        setCalStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch Cal.com status:', error);
      setError('Cal.com not configured');
    } finally {
      setLoading(false);
    }
  }

  async function fetchUpcomingBookings() {
    try {
      const response = await fetch('/cal/bookings');
      if (response.ok) {
        const data = await response.json();
        setBookings(data.bookings || []);
      }
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <Loader className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </div>
    );
  }

  if (error || !calStatus?.connected) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Cal.com Calendar</h2>
          </div>
        </div>
        <div className="px-6 py-8 text-center">
          <Calendar className="w-12 h-12 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-600">Cal.com not configured</p>
          <p className="text-sm text-gray-500 mt-1">Configure Cal.com to see your bookings</p>
          <a
            href="/dashboard/cal"
            className="inline-flex items-center mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Set Up Cal.com
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Cal.com Calendar</h2>
          </div>
          <a
            href="/dashboard/cal"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center"
          >
            Manage
            <ExternalLink className="w-3 h-3 ml-1" />
          </a>
        </div>
      </div>

      <div className="px-6 py-4">
        {/* Cal.com Status */}
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-green-800 font-medium">
              Connected to Cal.com
            </span>
          </div>
          <span className="text-xs text-green-600">
            {calStatus?.event_types?.length || 0} event types
          </span>
        </div>

        {/* Quick Info */}
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Username</span>
            </div>
            <span className="text-sm text-gray-900">{calStatus?.user?.username || 'Not set'}</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Event Types</span>
            </div>
            <span className="text-sm text-gray-900">
              {calStatus?.event_types?.length || 0} available
            </span>
          </div>
        </div>

        {/* Upcoming Bookings */}
        {bookings.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Upcoming Meetings</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {bookings.slice(0, 5).map((booking: CalBooking) => {
                const startDate = new Date(booking.startTime);
                const isToday = startDate.toDateString() === new Date().toDateString();

                return (
                  <div
                    key={booking.id}
                    className={`p-3 border rounded-lg ${isToday ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-gray-50'
                      }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{booking.title}</p>
                        <div className="flex items-center mt-1 text-xs text-gray-600">
                          <Calendar className="w-3 h-3 mr-1" />
                          <span>{startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                          <Clock className="w-3 h-3 ml-2 mr-1" />
                          <span>{startDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}</span>
                        </div>
                        {booking.attendees && booking.attendees.length > 0 && (
                          <div className="flex items-center mt-1 text-xs text-gray-600">
                            <User className="w-3 h-3 mr-1" />
                            <span>{booking.attendees[0].name}</span>
                          </div>
                        )}
                      </div>
                      <Video className="w-4 h-4 text-blue-600" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {bookings.length === 0 && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg text-center">
            <Calendar className="w-8 h-8 mx-auto text-gray-300 mb-2" />
            <p className="text-sm text-gray-600">No upcoming meetings</p>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <a
            href="/dashboard/cal"
            className="block w-full text-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all font-medium text-sm"
          >
            Create Booking Link
          </a>
        </div>
      </div>
    </div>
  );
}
