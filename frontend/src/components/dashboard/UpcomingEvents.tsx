import { useState, useEffect } from 'react';
import { Calendar, Clock, Phone, User, AlertCircle } from 'lucide-react';

interface Event {
  id: string;
  title: string;
  type: 'demo' | 'call' | 'followup' | 'meeting';
  scheduled_at: string;
  contact_name?: string;
  phone_number?: string;
  notes?: string;
}

export default function UpcomingEvents() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUpcomingEvents();
  }, []);

  async function fetchUpcomingEvents() {
    try {
      // TODO: Replace with actual API call when backend endpoint is ready
      // For now, using mock data
      const mockEvents: Event[] = [
        {
          id: '1',
          title: 'Product Demo',
          type: 'demo',
          scheduled_at: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
          contact_name: 'John Smith',
          phone_number: '+1234567890',
          notes: 'Interested in premium plan',
        },
        {
          id: '2',
          title: 'Follow-up Call',
          type: 'followup',
          scheduled_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
          contact_name: 'Sarah Johnson',
          phone_number: '+1987654321',
        },
        {
          id: '3',
          title: 'Consultation Call',
          type: 'call',
          scheduled_at: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(), // 2 days
          contact_name: 'Mike Davis',
          phone_number: '+1555666777',
        },
      ];
      
      setEvents(mockEvents);
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  function formatDateTime(dateString: string): { date: string; time: string; isToday: boolean; isTomorrow: boolean } {
    const date = new Date(dateString);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const eventDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    const isToday = eventDate.getTime() === today.getTime();
    const isTomorrow = eventDate.getTime() === tomorrow.getTime();

    let dateStr;
    if (isToday) {
      dateStr = 'Today';
    } else if (isTomorrow) {
      dateStr = 'Tomorrow';
    } else {
      dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

    return { date: dateStr, time: timeStr, isToday, isTomorrow };
  }

  function getEventTypeColor(type: string) {
    const colors = {
      demo: 'bg-purple-100 text-purple-800 border-purple-200',
      call: 'bg-blue-100 text-blue-800 border-blue-200',
      followup: 'bg-green-100 text-green-800 border-green-200',
      meeting: 'bg-orange-100 text-orange-800 border-orange-200',
    };
    return colors[type as keyof typeof colors] || colors.call;
  }

  function getEventIcon(type: string) {
    const icons = {
      demo: Calendar,
      call: Phone,
      followup: AlertCircle,
      meeting: User,
    };
    return icons[type as keyof typeof icons] || Phone;
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
            <h2 className="text-lg font-semibold text-gray-900">Upcoming Events</h2>
          </div>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All
          </button>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {events.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            <Calendar className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p>No upcoming events</p>
            <p className="text-sm mt-1">Your scheduled calls and demos will appear here</p>
          </div>
        ) : (
          events.map((event) => {
            const { date, time, isToday, isTomorrow } = formatDateTime(event.scheduled_at);
            const Icon = getEventIcon(event.type);
            const isUrgent = isToday || isTomorrow;

            return (
              <div
                key={event.id}
                className={`px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                  isUrgent ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start space-x-4">
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full border-2 ${getEventTypeColor(event.type)} flex items-center justify-center`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-gray-900 truncate">
                        {event.title}
                      </p>
                      {isUrgent && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
                          {date}
                        </span>
                      )}
                    </div>
                    
                    {event.contact_name && (
                      <p className="text-sm text-gray-600 mt-1">
                        <User className="w-3 h-3 inline mr-1" />
                        {event.contact_name}
                      </p>
                    )}
                    
                    {event.phone_number && (
                      <p className="text-xs text-gray-500 mt-1">
                        <Phone className="w-3 h-3 inline mr-1" />
                        {event.phone_number}
                      </p>
                    )}

                    <div className="flex items-center mt-2 text-xs text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      <span>{!isUrgent && date} at {time}</span>
                    </div>

                    {event.notes && (
                      <p className="text-xs text-gray-500 mt-2 italic">
                        {event.notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
