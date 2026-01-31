import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Phone, Clock, TrendingUp, MessageSquare } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';

interface CallData {
  id: string;
  to_number: string;
  from_number: string;
  status: string;
  duration: number;
  created_at: string;
  direction: string;
}

interface Analysis {
  summary: string;
  outcome: string;
  confidence_score: number;
  sentiment: string;
  key_points: string[];
  next_action: string;
}

interface Transcript {
  speaker: string;
  text: string;
  timestamp: string;
}

export default function CallDetails() {
  const { callId } = useParams();
  const navigate = useNavigate();
  const [call, setCall] = useState<CallData | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [loading, setLoading] = useState(true);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    if (callId) {
      fetchCallDetails();
    }
  }, [callId]);

  async function fetchCallDetails() {
    try {
      const token = localStorage.getItem('relayx_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      // Fetch call data
      const callRes = await fetch(`/calls/${callId}`, { headers });
      if (!callRes.ok) {
        throw new Error(`Failed to fetch call: ${callRes.status}`);
      }
      const callData = await callRes.json();
      setCall(callData);

      // Fetch analysis
      try {
        const analysisRes = await fetch(`/calls/${callId}/analysis`, { headers });
        if (analysisRes.ok) {
          const analysisData = await analysisRes.json();
          setAnalysis(analysisData);
        }
      } catch (e) {
        console.log('Analysis not available');
      }

      // Fetch transcripts
      const transcriptRes = await fetch(`/calls/${callId}/transcripts`, { headers });
      const transcriptData = await transcriptRes.json();
      setTranscripts(transcriptData);

      // Check for recording
      try {
        const recordingRes = await fetch(`/calls/${callId}/recording`, { method: 'HEAD', headers });
        if (recordingRes.ok) {
          setAudioUrl(`/calls/${callId}/recording`);
        }
      } catch (e) {
        console.log('Recording not available');
      }
    } catch (error) {
      console.error('Failed to fetch call details:', error);
    } finally {
      setLoading(false);
    }
  }

  function getOutcomeBadge(outcome: string) {
    if (!outcome) return null;

    const isPositive = outcome.toLowerCase().includes('interested') ||
      outcome.toLowerCase().includes('success') ||
      outcome.toLowerCase().includes('positive');
    const isNegative = outcome.toLowerCase().includes('not interested') ||
      outcome.toLowerCase().includes('declined');

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${isPositive ? 'bg-green-100 text-green-800' :
        isNegative ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
        {outcome}
      </span>
    );
  }

  function formatDuration(seconds: number) {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!call) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <p className="text-gray-600">Call not found</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-text">Call Details</h1>
            <p className="text-gray-400 mt-1">{call.to_number}</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center space-x-2 text-gray-600 mb-1">
              <Clock className="w-4 h-4" />
              <span className="text-sm font-medium">Duration</span>
            </div>
            <p className="text-2xl font-bold">{formatDuration(call.duration)}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center space-x-2 text-gray-600 mb-1">
              <Phone className="w-4 h-4" />
              <span className="text-sm font-medium">Status</span>
            </div>
            <p className="text-2xl font-bold capitalize">{call.status}</p>
          </div>
          {analysis && (
            <>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center space-x-2 text-gray-600 mb-1">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-sm font-medium">Confidence</span>
                </div>
                <p className="text-2xl font-bold">{Math.round(analysis.confidence_score * 100)}%</p>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center space-x-2 text-gray-600 mb-1">
                  <MessageSquare className="w-4 h-4" />
                  <span className="text-sm font-medium">Sentiment</span>
                </div>
                <p className="text-2xl font-bold capitalize">{analysis.sentiment || 'Neutral'}</p>
              </div>
            </>
          )}
        </div>

        {/* Analysis Summary */}
        {analysis && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Call Summary</h2>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-600 mb-2">Outcome</h3>
                {getOutcomeBadge(analysis.outcome)}
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-600 mb-2">Summary</h3>
                <p className="text-gray-800">{analysis.summary}</p>
              </div>

              {analysis.key_points && analysis.key_points.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">Key Points</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {analysis.key_points.map((point, i) => (
                      <li key={i} className="text-gray-800">{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              {analysis.next_action && (
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">Recommended Next Step</h3>
                  <p className="text-gray-800 bg-blue-50 p-3 rounded-lg">{analysis.next_action}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recording */}
        {audioUrl && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Call Recording</h2>
            <audio controls className="w-full">
              <source src={audioUrl} type="audio/wav" />
              Your browser does not support the audio element.
            </audio>
          </div>
        )}

        {/* Transcript */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Conversation Transcript</h2>

          {transcripts.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No transcript available</p>
          ) : (
            <div className="space-y-4">
              {transcripts.map((transcript, i) => (
                <div
                  key={i}
                  className={`flex ${transcript.speaker === 'agent' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-3 ${transcript.speaker === 'agent'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                      }`}
                  >
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-xs font-medium opacity-75">
                        {transcript.speaker === 'agent' ? 'Assistant' : 'Customer'}
                      </span>
                      <span className="text-xs opacity-50">
                        {new Date(transcript.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm">{transcript.text}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
