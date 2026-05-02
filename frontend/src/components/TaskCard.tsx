import React, { useState } from 'react';
import type { TaskLeaderboard } from '../types';
import { getMedalEmoji, getProgressBarColor } from '../utils/helpers';

interface TaskCardProps {
  task: TaskLeaderboard;
  maxScoresToShow?: number;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, maxScoresToShow = 5 }) => {
  const [showAll, setShowAll] = useState(false);
  const displayScores = showAll ? task.all_scores : task.all_scores.slice(0, maxScoresToShow);

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-md p-6 hover:shadow-xl transition-all border border-gray-100">
      <div className="mb-5">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-bold text-gray-900">{task.name}</h3>
          <span className="inline-flex items-center px-3 py-1 text-xs font-bold text-purple-700 bg-purple-100 rounded-full">
            {(task.weight * 100).toFixed(0)}% Weight
          </span>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed">{task.description}</p>
      </div>

      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {displayScores.map((entry, index) => (
          <div key={entry.model} className="bg-white rounded-lg p-3 border border-gray-100 hover:border-blue-200 transition-colors">
            <div className="flex items-center gap-3">
              <span className="text-2xl w-10 flex-shrink-0 text-center">
                {getMedalEmoji(index + 1)}
              </span>
              
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-semibold text-gray-900 text-sm truncate">
                    {entry.model_name}
                  </span>
                  <span className="font-bold text-lg text-gray-900 ml-2">
                    {entry.score.toFixed(1)}
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full transition-all ${getProgressBarColor(entry.score)}`}
                    style={{ width: `${entry.score}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {task.all_scores.length > maxScoresToShow && (
        <div className="mt-5 pt-4 border-t border-gray-200">
          <button
            onClick={() => setShowAll(!showAll)}
            className="w-full text-sm text-blue-600 hover:text-blue-800 font-semibold hover:bg-blue-50 py-2 rounded-lg transition-colors"
          >
            {showAll ? (
              <>Show less ↑</>
            ) : (
              <>View all {task.all_scores.length} models →</>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskCard;

// Made with Bob
