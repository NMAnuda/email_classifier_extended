export default function Tag({ label, confidence }) {
  const getColorClasses = (label) => {
    const colors = {
      spam: "bg-red-50 text-red-700 border-red-200",
      ham: "bg-green-50 text-green-700 border-green-200",
      promotion: "bg-purple-50 text-purple-700 border-purple-200",
      promotions: "bg-purple-50 text-purple-700 border-purple-200",
      social: "bg-blue-50 text-blue-700 border-blue-200",
      business: "bg-indigo-50 text-indigo-700 border-indigo-200",
      education: "bg-cyan-50 text-cyan-700 border-cyan-200",
      personal: "bg-orange-50 text-orange-700 border-orange-200",
    };
    return colors[label?.toLowerCase()] || "bg-gray-50 text-gray-700 border-gray-200";
  };

  return (
    <div className="flex items-center gap-2">
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getColorClasses(label)}`}>
        {label || "Unknown"}
      </span>
      {confidence && (
        <span className="text-xs text-gray-500 font-medium">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </div>
  );
}