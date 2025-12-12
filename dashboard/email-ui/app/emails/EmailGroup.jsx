"use client";

import { useState } from "react";
import EmailCard from "./EmailCard";
import { ChevronDown, ChevronUp } from "lucide-react";

export default function EmailGroup({ topic, emails, icon: Icon }) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex justify-between items-center p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Icon className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-left">
            <h2 className="text-base font-semibold text-gray-900">{topic}</h2>
            <p className="text-xs text-gray-500">{emails.length} emails</p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>
      
      {isExpanded && (
        <div className="border-t border-gray-100 p-4 bg-gray-50 space-y-2">
          {emails.map((email, idx) => (
            <EmailCard key={idx} email={email} />
          ))}
        </div>
      )}
    </div>
  );
}