import React from 'react';
import type { CategoryLeaderboardEntry } from '../types';
import { getMedalEmoji } from '../utils/helpers';

interface CategoryLeaderboardProps {
  categoryName: string;
  categoryDescription: string;
  leaderboard: CategoryLeaderboardEntry[];
  loading: boolean;
}

const CategoryLeaderboard: React.FC<CategoryLeaderboardProps> = ({
  categoryName,
  categoryDescription,
  leaderboard,
  loading,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading {categoryName} leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          🏆 {categoryName} Leaderboard
        </h2>
        <p className="text-blue-100 text-sm mt-1">{categoryDescription}</p>
      </div>
      <div className="p-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase">
                  Rank
                </th>
                <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase">
                  Model
                </th>
                <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase">
                  Provider
                </th>
                <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase">
                  {categoryName} Score
                </th>
                <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase">
                  RCA Score
                </th>
                <th className="px-4 py-4 text-left text-sm font-semibold text-gray-700 uppercase">
                  Key Benchmarks
                </th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry) => (
                <tr
                  key={entry.model.id}
                  className="border-b border-gray-100 hover:bg-blue-50 transition-colors"
                >
                  <td className="px-4 py-5">
                    <div className="flex items-center gap-2">
                      <span className="text-3xl">{getMedalEmoji(entry.rank)}</span>
                      <span className="text-lg font-bold text-gray-900">
                        #{entry.rank}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-5">
                    <div>
                      <div className="font-semibold text-gray-900 text-base">
                        {entry.model.name}
                      </div>
                      <div className="text-sm text-gray-500 mt-1">
                        {entry.model.version}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-5">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                      {entry.model.provider}
                    </span>
                  </td>
                  <td className="px-4 py-5">
                    <div className="flex items-center gap-2">
                      <div className={`
                        px-4 py-2 rounded-lg font-bold text-lg
                        ${entry.score >= 90 ? 'bg-green-100 text-green-800' :
                          entry.score >= 80 ? 'bg-blue-100 text-blue-800' :
                          entry.score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'}
                      `}>
                        {entry.score.toFixed(1)}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-5">
                    <span className="text-sm font-medium text-gray-600">
                      {entry.rca_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-5">
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(entry.key_benchmarks).map(([name, score]) => (
                        <div
                          key={name}
                          className="px-2 py-1 bg-gray-50 rounded text-xs"
                          title={name}
                        >
                          <span className="font-medium text-gray-700">{name.split('_')[0]}</span>
                          <span className="text-gray-500 ml-1">{score.toFixed(0)}</span>
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default CategoryLeaderboard;

// Made with Bob
