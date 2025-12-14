"use client";

import { useState } from "react";
import Tag from "./Tag";
import { Mail, ChevronDown, ChevronUp, Send, X, User, Clock, Tag as TagIcon, AlertTriangle } from "lucide-react";
import axios from "axios";

export default function EmailCard({ email, onGenerateReply }) {
  const [showBody, setShowBody] = useState(false);
  const [showFullBody, setShowFullBody] = useState(false);
  const [showReplyModal, setShowReplyModal] = useState(false);
  const [replyDraft, setReplyDraft] = useState('');
  const [replyLoading, setReplyLoading] = useState(false);
  const [sendLoading, setSendLoading] = useState(false);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

  const previewBody = email.body 
    ? email.body.substring(0, 120) + (email.body.length > 120 ? '...' : '') 
    : "No message content available";

  const summaryBody = email.body 
    ? email.body.split(/[.!?]+/).slice(0, 3).filter(s => s.trim()).join('. ') + '.' 
    : "No message content available";

  const isRepliable = (email.type === 'inbox')
    && !['spam', 'promotion', 'promotions'].includes((email.predicted_label || '').toLowerCase()) 
    && (email.confidence || 0) >= 0.7
    && email.from !== email.to;

  const getPriorityBadge = () => {
    const priority = email.priority || 'medium';
    const sentiment = email.sentiment || 'neutral';
    let icon = null;
    let color = 'bg-gray-100 text-gray-600';
    if (priority === 'high' || sentiment === 'negative') {
      icon = <AlertTriangle className="w-3 h-3" />;
      color = 'bg-red-100 text-red-700';
    } else if (priority === 'low' || sentiment === 'positive') {
      color = 'bg-green-100 text-green-700';
    }
    return (
      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${color}`}>
        {icon}
        {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
      </div>
    );
  };

  const generateReply = async () => {
    setReplyLoading(true);
    try {
      const response = await axios.post(`${backendUrl}/api/email/reply`, {
        email_text: `${email.subject}\n\n${email.body}`,
        label: email.predicted_label,
        confidence: email.confidence
      });

      setReplyDraft(response.data.draft);
      setShowReplyModal(true);
      
      if (onGenerateReply) onGenerateReply(email.message_id);
    } catch (error) {
      console.error('Reply generation failed:', error);
      alert('Failed to generate reply. Check backend connection.');
    } finally {
      setReplyLoading(false);
    }
  };

  const sendReply = async () => {
    if (!replyDraft.trim()) return alert('Draft is empty—add a message first!');

    setSendLoading(true);
    try {
      const response = await axios.post(`${backendUrl}/api/email/send_reply`, {
        message_id: email.message_id,
        draft_text: replyDraft,
        subject: email.subject
      });

      if (response.data.success) {
        alert(`Reply sent successfully!`);
        setShowReplyModal(false);
        setReplyDraft('');
        if (onGenerateReply) onGenerateReply(email.message_id, true);
      }
    } catch (error) {
      console.error('Send failed:', error);
      alert(`Failed to send: ${error.response?.data?.error || 'Check Gmail auth'}`);
    } finally {
      setSendLoading(false);
    }
  };

  return (
    <>
      <div className="border border-gray-200 rounded-xl overflow-hidden bg-white hover:shadow-md transition-shadow duration-200">
        {/* Header Section */}
        <div className="p-4">
          <div className="flex justify-between items-start gap-4 mb-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-2 mb-1">
                <Mail className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                <h2 className="text-base font-semibold text-gray-900 line-clamp-2">
                  {email.subject || "(No Subject)"}
                </h2>
              </div>
              <div className="flex gap-4 text-xs text-gray-500 ml-7 mt-1">
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  <span>From: {email.from || 'Unknown'}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  <span>To: {email.to || 'You'}</span>
                </div>
              </div>
              {email.sentiment && <div className="ml-7 mt-1">{getPriorityBadge()}</div>}
            </div>
            <Tag label={email.predicted_label} confidence={email.confidence} />
          </div>

          <p className="text-gray-600 text-sm leading-relaxed line-clamp-2 ml-7">
            {previewBody}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="px-4 pb-3 flex items-center justify-between border-t border-gray-100 pt-3">
          <button
            onClick={() => setShowBody(!showBody)}
            className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            {showBody ? (<><ChevronUp className="w-4 h-4" />Hide Details</>) : (<><ChevronDown className="w-4 h-4" />View Details</>)}
          </button>

          <div className="flex items-center gap-2">
            {isRepliable ? (
              <button
                onClick={generateReply}
                disabled={replyLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-sm font-medium hover:bg-green-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
                {replyLoading ? "Generating..." : "Reply"}
              </button>
            ) : (
              <span className="text-xs text-gray-400 italic">
                {email.type === 'sent' ? "Sent" : "Review only"}
              </span>
            )}
          </div>
        </div>

        {/* Expandable Details */}
        {showBody && (
          <div className="border-t border-gray-100 bg-gray-50">
            <div className="p-4 space-y-3">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <TagIcon className="w-4 h-4 text-blue-600" />
                  <h3 className="text-sm font-semibold text-gray-900">Summary</h3>
                </div>
                <p className="text-gray-700 text-sm leading-relaxed">{summaryBody}</p>
              </div>

              {email.body && email.body.length > 200 && (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <button
                    onClick={() => setShowFullBody(!showFullBody)}
                    className="w-full px-4 py-3 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <span>Full Message Content</span>
                    {showFullBody ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  {showFullBody && (
                    <div className="px-4 pb-4 pt-2 border-t border-gray-100 max-h-64 overflow-y-auto">
                      <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap break-words">{email.body}</p>
                    </div>
                  )}
                </div>
              )}

              {email.cleaned_text && (
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <h3 className="text-sm font-semibold text-gray-900">Processed Text</h3>
                  </div>
                  <p className="text-gray-600 text-xs leading-relaxed font-mono max-h-24 overflow-auto">
                    {email.cleaned_text.substring(0, 300)}{email.cleaned_text.length > 300 ? '...' : ''}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Reply Modal */}
      {showReplyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full shadow-2xl">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Reply Draft</h3>
                <p className="text-sm text-gray-500 mt-1">Re: {email.subject || "(No Subject)"}</p>
              </div>
              <button 
                onClick={() => { setShowReplyModal(false); setReplyDraft(''); }}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <textarea
                value={replyDraft}
                onChange={(e) => setReplyDraft(e.target.value)}
                placeholder="Write your reply here..."
                className="w-full h-48 p-4 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-xl">
              <button
                onClick={() => { setShowReplyModal(false); setReplyDraft(''); }}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
              >
                Discard
              </button>
              <button
                onClick={sendReply}
                disabled={sendLoading || !replyDraft.trim()}
                className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
                {sendLoading ? "Sending..." : "Send Reply"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
