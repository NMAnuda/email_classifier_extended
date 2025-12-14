"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { Mail, Inbox, Send as SendIcon, RefreshCw, AlertCircle, Briefcase, BarChart3 } from "lucide-react";
import EmailGroup from "./EmailGroup";

// StatCard Component
function StatCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

export default function EmailsPage() {
  const [emails, setEmails] = useState([]);       // Inbox
  const [sentEmails, setSentEmails] = useState([]); // Sent
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('inbox');

  const timeoutRef = useRef(null);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  const fetchEmails = async (type = 'inbox') => {
    try {
      setLoading(true);
      setError(null);
      const endpoint = type === 'sent' ? 'sent' : 'pull';
      const res = await axios.get(`${backendUrl}/api/email/${endpoint}?limit=15`);
      if (type === 'inbox') setEmails(res.data);
      else setSentEmails(res.data);
    } catch (error) {
      console.error(`Failed to fetch ${type}:`, error);
      setError(`Network error fetching ${type}: ${error.message}. Check backend service.`);
    } finally {
      setLoading(false);
    }
  };

  const refreshCurrent = useCallback((type) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => fetchEmails(type), 300);
  }, []);

  useEffect(() => {
    fetchEmails(activeTab);

    const interval = setInterval(() => fetchEmails(activeTab), 30000); // Auto-refresh every 30s

    return () => {
      clearInterval(interval);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [activeTab]);

  const handleRefresh = () => refreshCurrent(activeTab);

  const groupedEmails = (emailsList) => emailsList.reduce((acc, email) => {
    const label = email.predicted_label || "Unknown";
    acc[label] = acc[label] || [];
    acc[label].push(email);
    return acc;
  }, {});

  const inboxGroups = groupedEmails(emails);
  const sentGroups = groupedEmails(sentEmails);

  const totalEmails = emails.length;
  const spamCount = emails.filter(e => e.predicted_label === 'spam').length;
  const businessCount = emails.filter(e => e.predicted_label === 'business').length;
  const avgConfidence = emails.length > 0 
    ? (emails.reduce((sum, e) => sum + (e.confidence || 0), 0) / emails.length * 100).toFixed(1)
    : 0;

  const currentEmails = activeTab === 'inbox' ? emails : sentEmails;
  const currentGroups = activeTab === 'inbox' ? inboxGroups : sentGroups;
  const currentTitle = activeTab === 'inbox' ? 'Inbox' : 'Sent';
  const showStats = activeTab === 'inbox';

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Classification Dashboard</h1>
              <p className="text-gray-600">Organize and analyze your emails with AI-powered classification</p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-400 transition-colors shadow-sm font-medium"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 rounded-t-lg overflow-hidden">
            {['inbox', 'sent'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-6 font-medium text-sm flex-1 ${
                  activeTab === tab 
                    ? 'bg-white border-b-2 border-blue-500 text-blue-600 shadow-sm' 
                    : 'bg-gray-50 text-gray-500 hover:text-gray-700 hover:bg-white transition-colors'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  {tab === 'inbox' ? <Inbox className="w-4 h-4" /> : <SendIcon className="w-4 h-4" />}
                  {tab.charAt(0).toUpperCase() + tab.slice(1)} ({currentEmails.length})
                </div>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded-lg">
            <p>{error}</p>
            <button onClick={handleRefresh} className="mt-2 px-4 py-2 bg-yellow-500 text-white rounded">
              Retry Fetch
            </button>
          </div>
        )}

        {currentEmails.length > 0 && (
          <>
            {/* Stats */}
            {showStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <StatCard label="Total Emails" value={totalEmails} icon={Inbox} color="bg-blue-50 text-blue-600" />
                <StatCard label="Spam Detected" value={spamCount} icon={AlertCircle} color="bg-red-50 text-red-600" />
                <StatCard label="Business" value={businessCount} icon={Briefcase} color="bg-green-50 text-green-600" />
                <StatCard label="Avg Confidence" value={`${avgConfidence}%`} icon={BarChart3} color="bg-purple-50 text-purple-600" />
              </div>
            )}

            {/* Email Groups */}
            <div className="space-y-4">
              {Object.entries(currentGroups).map(([topic, topicEmails]) => (
                <EmailGroup 
                  key={topic} 
                  topic={topic.charAt(0).toUpperCase() + topic.slice(1)} 
                  emails={topicEmails}
                  icon={Mail}
                />
              ))}
            </div>
          </>
        )}

        {currentEmails.length === 0 && !loading && (
          <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-200">
            <Mail className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Emails in {currentTitle}</h3>
            <p className="text-gray-600 mb-6">
              {currentTitle === 'Sent' ? 'No sent emails found.' : 'Click Refresh to load and classify your emails'}
            </p>
            <button
              onClick={() => fetchEmails(activeTab)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Load {currentTitle}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
