import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { TaskLeaderboard, LeaderboardEntry, Category, CategoryLeaderboardEntry } from '../types';
import TaskCard from '../components/TaskCard';
import RCAScoreBadge from '../components/RCAScoreBadge';
import AddModelModal from '../components/AddModelModal';
import CategorySelector from '../components/CategorySelector';
import CategoryLeaderboard from '../components/CategoryLeaderboard';
import RefreshStatus from '../components/RefreshStatus';
import { getMedalEmoji } from '../utils/helpers';

const Dashboard: React.FC = () => {
  const [tasks, setTasks] = useState<TaskLeaderboard[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [categories, setCategories] = useState<Record<string, Category>>({});
  const [activeCategory, setActiveCategory] = useState<string>('rca');
  const [categoryLeaderboard, setCategoryLeaderboard] = useState<CategoryLeaderboardEntry[]>([]);
  const [categoryLoading, setCategoryLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deletingModelId, setDeletingModelId] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [tasksData, leaderboardData, categoriesData] = await Promise.all([
        apiService.getTasks(),
        apiService.getLeaderboard(),
        apiService.getCategories()
      ]);
      setTasks(tasksData.tasks);
      setLeaderboard(leaderboardData.leaderboard);
      setCategories(categoriesData.categories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategoryLeaderboard = async (category: string) => {
    try {
      setCategoryLoading(true);
      const data = await apiService.getCategoryLeaderboard(category);
      setCategoryLeaderboard(data.leaderboard);
    } catch (err) {
      console.error('Failed to fetch category leaderboard:', err);
    } finally {
      setCategoryLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeCategory) {
      fetchCategoryLeaderboard(activeCategory);
    }
  }, [activeCategory]);

  const handleCategoryChange = (categoryId: string) => {
    setActiveCategory(categoryId);
  };

  const handleModalSuccess = () => {
    fetchData(); // Refresh data after adding a model
  };

  const handleDeleteModel = async (modelId: string, modelName: string) => {
    if (!confirm(`Are you sure you want to delete "${modelName}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingModelId(modelId);
    try {
      const response = await apiService.deleteUserModel(modelId);
      if (response.success) {
        // Refresh data after successful deletion
        await fetchData();
        alert(`✅ ${response.message}`);
      }
    } catch (err: any) {
      alert(`❌ Failed to delete model: ${err.response?.data?.detail || err.message}`);
    } finally {
      setDeletingModelId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-bold text-lg mb-2">Error Loading Dashboard</h2>
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-gray-100">
      {/* Add Model Modal */}
      <AddModelModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
      />

      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="px-8 py-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                🎯 AI Model Leaderboard
              </h1>
              <p className="text-lg text-gray-600">
                Comprehensive evaluation of LLM models across RCA, Coding, Reasoning, and General capabilities
              </p>
            </div>
            <div className="flex flex-col items-end gap-4">
              {/* Top Row: Add Model Button and Total Models */}
              <div className="flex items-center gap-6">
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all font-medium shadow-lg hover:shadow-xl flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Your Model
                </button>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Total Models</div>
                  <div className="text-3xl font-bold text-blue-600">{leaderboard.length}</div>
                </div>
              </div>
              
              {/* Bottom Row: Refresh Status */}
              <div className="bg-gray-50 rounded-lg px-4 py-3 border border-gray-200">
                <RefreshStatus />
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="px-8 py-8">
        {/* Category Selector */}
        {Object.keys(categories).length > 0 && (
          <CategorySelector
            categories={categories}
            activeCategory={activeCategory}
            onCategoryChange={handleCategoryChange}
          />
        )}

        <div className="grid grid-cols-12 gap-8">
          {/* Left Column - Category Leaderboard (takes 8 columns) */}
          <section className="col-span-8">
            <CategoryLeaderboard
              categoryName={categories[activeCategory]?.name || 'Loading...'}
              categoryDescription={categories[activeCategory]?.description || ''}
              leaderboard={categoryLeaderboard}
              loading={categoryLoading}
            />
          </section>

          {/* Right Column - Stats & Info (takes 4 columns) - Only show for RCA */}
          {activeCategory === 'rca' && (
            <aside className="col-span-4 space-y-6">
              {/* Stats Card */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">📈 RCA Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Total Tasks</span>
                    <span className="text-xl font-bold text-blue-600">{tasks.length}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Top Score</span>
                    <span className="text-xl font-bold text-green-600">
                      {leaderboard[0]?.rca_score.toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Avg Score</span>
                    <span className="text-xl font-bold text-purple-600">
                      {(leaderboard.reduce((sum, e) => sum + e.rca_score, 0) / leaderboard.length).toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Info Card */}
              <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl shadow-lg p-6 text-white">
                <h3 className="text-lg font-bold mb-3">ℹ️ About RCA Score</h3>
                <p className="text-sm text-blue-100 leading-relaxed">
                  The RCA (Root Cause Analysis) score measures a model's ability to identify,
                  analyze, and explain the root causes of problems across various tasks.
                </p>
              </div>
            </aside>
          )}

          {/* Right Column - Category Info (takes 4 columns) - Show for non-RCA categories */}
          {activeCategory !== 'rca' && (
            <aside className="col-span-4 space-y-6">
              {/* Category Info Card */}
              <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl shadow-lg p-6 text-white">
                <h3 className="text-lg font-bold mb-3">
                  {categories[activeCategory]?.icon} About {categories[activeCategory]?.name}
                </h3>
                <p className="text-sm text-purple-100 leading-relaxed mb-4">
                  {categories[activeCategory]?.description}
                </p>
              </div>

              {/* Category Stats Card */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Category Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Models Ranked</span>
                    <span className="text-xl font-bold text-blue-600">{categoryLeaderboard.length}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Top Score</span>
                    <span className="text-xl font-bold text-green-600">
                      {categoryLeaderboard[0]?.score.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Avg Score</span>
                    <span className="text-xl font-bold text-purple-600">
                      {categoryLeaderboard.length > 0
                        ? (categoryLeaderboard.reduce((sum, e) => sum + e.score, 0) / categoryLeaderboard.length).toFixed(1)
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Leader Card */}
              {categoryLeaderboard[0] && (
                <div className="bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-xl shadow-lg p-6 text-gray-900">
                  <h3 className="text-lg font-bold mb-3">🏆 Current Leader</h3>
                  <div className="text-2xl font-bold mb-1">{categoryLeaderboard[0].model.name}</div>
                  <div className="text-sm opacity-80 mb-2">{categoryLeaderboard[0].model.provider}</div>
                  <div className="text-3xl font-bold">{categoryLeaderboard[0].score.toFixed(1)}</div>
                </div>
              )}
            </aside>
          )}
        </div>

        {/* Task Leaderboards Section - Full Width - Only show for RCA category */}
        {activeCategory === 'rca' && (
          <section className="mt-8">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  📊 Task-Based Performance
                </h2>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {tasks.map((task) => (
                    <TaskCard key={task.id} task={task} maxScoresToShow={5} />
                  ))}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Benchmark Details Section - Show for non-RCA categories */}
        {activeCategory !== 'rca' && categoryLeaderboard.length > 0 && (
          <section className="mt-8">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  📊 Key Benchmarks for {categories[activeCategory]?.name}
                </h2>
              </div>
              <div className="p-6">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b-2 border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Model</th>
                        {activeCategory === 'general' && (
                          <>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">MMLU<br/><span className="text-xs font-normal text-gray-500">(Knowledge)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">ARC<br/><span className="text-xs font-normal text-gray-500">(Reasoning)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">GSM8K<br/><span className="text-xs font-normal text-gray-500">(Math)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">HumanEval<br/><span className="text-xs font-normal text-gray-500">(Coding)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">TruthfulQA<br/><span className="text-xs font-normal text-gray-500">(Truth)</span></th>
                          </>
                        )}
                        {activeCategory === 'coding' && (
                          <>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">HumanEval<br/><span className="text-xs font-normal text-gray-500">(Code Gen)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">MBPP<br/><span className="text-xs font-normal text-gray-500">(Python)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">ARC<br/><span className="text-xs font-normal text-gray-500">(Reasoning)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">GSM8K<br/><span className="text-xs font-normal text-gray-500">(Problem Solving)</span></th>
                          </>
                        )}
                        {activeCategory === 'reasoning' && (
                          <>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">ARC<br/><span className="text-xs font-normal text-gray-500">(Logical)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">HellaSwag<br/><span className="text-xs font-normal text-gray-500">(Commonsense)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">GSM8K<br/><span className="text-xs font-normal text-gray-500">(Math)</span></th>
                            <th className="text-center py-3 px-4 font-semibold text-gray-700">MMLU<br/><span className="text-xs font-normal text-gray-500">(Knowledge)</span></th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {categoryLeaderboard.map((entry, idx) => (
                        <tr key={entry.model.id} className={`border-b border-gray-100 ${idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{idx < 3 ? getMedalEmoji(idx + 1) : `#${idx + 1}`}</span>
                              <div>
                                <div className="font-semibold text-gray-900">{entry.model.name}</div>
                                <div className="text-xs text-gray-500">{entry.model.provider}</div>
                              </div>
                            </div>
                          </td>
                          {activeCategory === 'general' && (
                            <>
                              <td className="text-center py-3 px-4 font-semibold text-blue-600">{entry.key_benchmarks.mmlu?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-green-600">{entry.key_benchmarks.arc_challenge?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-purple-600">{entry.key_benchmarks.gsm8k?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-orange-600">{entry.key_benchmarks.humaneval?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-red-600">{entry.key_benchmarks.truthfulqa?.toFixed(1) || 'N/A'}</td>
                            </>
                          )}
                          {activeCategory === 'coding' && (
                            <>
                              <td className="text-center py-3 px-4 font-semibold text-blue-600">{entry.key_benchmarks.humaneval?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-green-600">{entry.key_benchmarks.mbpp?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-purple-600">{entry.key_benchmarks.arc_challenge?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-orange-600">{entry.key_benchmarks.gsm8k?.toFixed(1) || 'N/A'}</td>
                            </>
                          )}
                          {activeCategory === 'reasoning' && (
                            <>
                              <td className="text-center py-3 px-4 font-semibold text-blue-600">{entry.key_benchmarks.arc_challenge?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-green-600">{entry.key_benchmarks.hellaswag?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-purple-600">{entry.key_benchmarks.gsm8k?.toFixed(1) || 'N/A'}</td>
                              <td className="text-center py-3 px-4 font-semibold text-orange-600">{entry.key_benchmarks.mmlu?.toFixed(1) || 'N/A'}</td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-700">
                    <strong>Note:</strong> These benchmarks are weighted differently for the {categories[activeCategory]?.name} category score.
                    Higher scores indicate better performance.
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="px-8 py-4">
          <p className="text-center text-sm text-gray-600">
            AI Model Leaderboard <span className="font-semibold text-blue-600">v2.0.0</span> •
            Multi-source validation
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;

// Made with Bob
