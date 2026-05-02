import React, { useState } from 'react';
import { apiService } from '../services/api';
import type { UserModelInput, TaskScore, ModelMetadata } from '../types';

interface AddModelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type InputMode = 'huggingface' | 'manual';

const AddModelModal: React.FC<AddModelModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState<InputMode>('huggingface');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [hfUrl, setHfUrl] = useState('');
  const [hfPreview, setHfPreview] = useState<any>(null);

  // Form state for manual input
  const [formData, setFormData] = useState<UserModelInput>({
    name: '',
    provider: '',
    version: '',
    task_scores: {
      code_understanding: 0,
      log_analysis: 0,
      metric_interpretation: 0,
      causal_reasoning: 0,
      pattern_recognition: 0,
      context_synthesis: 0,
      root_cause_identification: 0,
      solution_recommendation: 0,
    },
    metadata: {
      parameters: '',
      context_window: 0,
      release_date: '',
    },
  });

  const taskFields: Array<{ key: keyof TaskScore; label: string; description: string }> = [
    { key: 'code_understanding', label: 'Code Understanding', description: 'Ability to comprehend code structure and logic' },
    { key: 'log_analysis', label: 'Log Analysis', description: 'Skill in parsing and interpreting system logs' },
    { key: 'metric_interpretation', label: 'Metric Interpretation', description: 'Understanding of performance metrics' },
    { key: 'causal_reasoning', label: 'Causal Reasoning', description: 'Logical deduction of cause-effect relationships' },
    { key: 'pattern_recognition', label: 'Pattern Recognition', description: 'Identifying recurring issues and patterns' },
    { key: 'context_synthesis', label: 'Context Synthesis', description: 'Combining multiple data sources' },
    { key: 'root_cause_identification', label: 'Root Cause Identification', description: 'Pinpointing the underlying issue' },
    { key: 'solution_recommendation', label: 'Solution Recommendation', description: 'Suggesting effective fixes' },
  ];

  const handleInputChange = (field: keyof UserModelInput, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleTaskScoreChange = (task: keyof TaskScore, value: number) => {
    setFormData((prev) => ({
      ...prev,
      task_scores: { ...prev.task_scores, [task]: value },
    }));
  };

  const handleMetadataChange = (field: keyof ModelMetadata, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      metadata: { ...prev.metadata, [field]: value },
    }));
  };

  const handleFetchFromHuggingFace = async () => {
    if (!hfUrl.trim()) {
      setError('Please enter a HuggingFace URL');
      return;
    }

    setLoading(true);
    setError(null);
    setHfPreview(null);

    try {
      const response = await apiService.fetchFromHuggingFace(hfUrl);
      if (response.success) {
        // Check if model is suitable for RCA
        if (response.suitable_for_rca === false) {
          setError(response.rejection_reason || response.message || 'This model is not suitable for RCA tasks');
          setHfPreview(null);
        } else if (response.confidence === 'very_low') {
          // Show warning for models with no benchmark data
          setError(null);
          setHfPreview(response);
        } else {
          setHfPreview(response);
          setError(null);
        }
      } else {
        setError(response.message || 'Failed to fetch model');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch model from HuggingFace');
    } finally {
      setLoading(false);
    }
  };

  const handleAddFromHuggingFace = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.addFromHuggingFace(hfUrl);
      if (response.success) {
        setSuccess(response.message);
        setTimeout(() => {
          onSuccess();
          handleClose();
        }, 2000);
      } else {
        setError(response.message || 'Failed to add model');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to add model');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiService.addUserModel(formData);
      if (response.success) {
        setSuccess(response.message);
        setTimeout(() => {
          onSuccess();
          handleClose();
        }, 2000);
      } else {
        setError(response.message || 'Failed to add model');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to add model');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setMode('huggingface');
    setHfUrl('');
    setHfPreview(null);
    setFormData({
      name: '',
      provider: '',
      version: '',
      task_scores: {
        code_understanding: 0,
        log_analysis: 0,
        metric_interpretation: 0,
        causal_reasoning: 0,
        pattern_recognition: 0,
        context_synthesis: 0,
        root_cause_identification: 0,
        solution_recommendation: 0,
      },
      metadata: {
        parameters: '',
        context_window: 0,
        release_date: '',
      },
    });
    setError(null);
    setSuccess(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={handleClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
            <div className="flex items-center justify-between">
              <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                ➕ Add New Model for RCA Testing
              </h3>
              <button
                onClick={handleClose}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white px-6 py-6">
            {/* Success/Error Messages */}
            {success && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 font-medium">✅ {success}</p>
              </div>
            )}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 font-medium">❌ {error}</p>
              </div>
            )}

            {/* Mode Selector */}
            <div className="mb-6 flex gap-2 p-1 bg-gray-100 rounded-lg">
              <button
                type="button"
                onClick={() => {
                  setMode('huggingface');
                  setError(null);
                }}
                className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
                  mode === 'huggingface'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                🤗 From HuggingFace
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('manual');
                  setError(null);
                  setHfPreview(null);
                }}
                className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
                  mode === 'manual'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                ✍️ Manual Input
              </button>
            </div>

            {/* HuggingFace Mode */}
            {mode === 'huggingface' && (
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    Enter a HuggingFace model URL and we'll automatically fetch benchmarks and calculate RCA scores based on available data.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    HuggingFace Model URL *
                  </label>
                  <input
                    type="text"
                    value={hfUrl}
                    onChange={(e) => setHfUrl(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro"
                    disabled={loading}
                  />
                </div>

                <button
                  type="button"
                  onClick={handleFetchFromHuggingFace}
                  disabled={loading || !hfUrl.trim()}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Fetching...
                    </>
                  ) : (
                    <>
                      🔍 Fetch Model Info
                    </>
                  )}
                </button>

                {/* Preview */}
                {hfPreview && (
                  <div className="mt-4 space-y-4 max-h-[50vh] overflow-y-auto">
                    {/* Low Confidence Warning */}
                    {hfPreview.confidence === 'very_low' ? (
                      <>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h4 className="font-bold text-green-900 mb-2">✅ Model Found!</h4>
                          <div className="space-y-2 text-sm">
                            <p><strong>Name:</strong> {hfPreview.model_info?.name}</p>
                            <p><strong>Provider:</strong> {hfPreview.model_info?.provider}</p>
                            <p><strong>Parameters:</strong> {hfPreview.model_info?.parameters}</p>
                            <p><strong>Context Window:</strong> {hfPreview.model_info?.context_window?.toLocaleString()}</p>
                          </div>
                        </div>

                        <div className="bg-red-50 border-2 border-red-300 rounded-lg p-5">
                          <div className="flex items-start gap-3">
                            <div className="text-3xl">🚫</div>
                            <div className="flex-1">
                              <h4 className="font-bold text-red-900 text-lg mb-2">Not Safe for RCA</h4>
                              <p className="text-red-800 font-medium mb-2">{hfPreview.warning}</p>
                              <p className="text-sm text-red-700 mb-3">{hfPreview.message}</p>
                              <div className="bg-red-100 rounded-lg p-3 border border-red-200">
                                <p className="text-sm font-semibold text-red-900 mb-1">⚠️ Confidence Level: Very Low</p>
                                <p className="text-xs text-red-700">
                                  Without benchmark data, we cannot reliably calculate RCA scores for this model.
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h4 className="font-bold text-blue-900 mb-2">💡 Recommendation</h4>
                          <p className="text-sm text-blue-800 mb-3">
                            To add this model with accurate RCA scores, please switch to <strong>Manual Input</strong> mode
                            and provide the task scores based on your own evaluation or testing.
                          </p>
                          <button
                            type="button"
                            onClick={() => {
                              setMode('manual');
                              setHfPreview(null);
                            }}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                          >
                            Switch to Manual Input
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h4 className="font-bold text-green-900 mb-2">✅ Model Found!</h4>
                          <div className="space-y-2 text-sm">
                            <p><strong>Name:</strong> {hfPreview.model_info?.name}</p>
                            <p><strong>Provider:</strong> {hfPreview.model_info?.provider}</p>
                            <p><strong>Parameters:</strong> {hfPreview.model_info?.parameters}</p>
                            <p><strong>Context Window:</strong> {hfPreview.model_info?.context_window?.toLocaleString()}</p>
                          </div>
                        </div>

                        {hfPreview.benchmarks && Object.keys(hfPreview.benchmarks).length > 0 && (
                          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <h4 className="font-bold text-purple-900 mb-2">
                              📊 Benchmarks Found ({Object.keys(hfPreview.benchmarks).length})
                            </h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {Object.entries(hfPreview.benchmarks).map(([name, score]: [string, any]) => (
                                <div key={name} className="flex justify-between">
                                  <span className="text-gray-700">{name}:</span>
                                  <span className="font-medium">{score.toFixed(1)}%</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Confidence Badge */}
                        {hfPreview.confidence && (
                          <div className={`rounded-lg p-3 border ${
                            hfPreview.confidence === 'high'
                              ? 'bg-green-50 border-green-200'
                              : hfPreview.confidence === 'medium'
                              ? 'bg-yellow-50 border-yellow-200'
                              : 'bg-orange-50 border-orange-200'
                          }`}>
                            <p className={`text-sm font-medium ${
                              hfPreview.confidence === 'high'
                                ? 'text-green-800'
                                : hfPreview.confidence === 'medium'
                                ? 'text-yellow-800'
                                : 'text-orange-800'
                            }`}>
                              {hfPreview.confidence === 'high' && '✅ High Confidence'}
                              {hfPreview.confidence === 'medium' && '⚠️ Medium Confidence'}
                              {hfPreview.confidence === 'low' && '⚠️ Low Confidence'}
                              {' - '}Based on {Object.keys(hfPreview.benchmarks || {}).length} benchmark(s)
                            </p>
                          </div>
                        )}

                        <div className="bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                          <h4 className="font-bold text-blue-900 mb-3">🎯 Calculated RCA Scores</h4>
                          <div className="space-y-2">
                            {Object.entries(hfPreview.task_scores || {}).map(([task, score]: [string, any]) => (
                              <div key={task} className="flex items-center justify-between">
                                <span className="text-sm text-gray-700 capitalize">
                                  {task.replace(/_/g, ' ')}:
                                </span>
                                <span className="font-bold text-blue-600">{score.toFixed(1)}/100</span>
                              </div>
                            ))}
                          </div>
                          <div className="mt-4 pt-4 border-t border-blue-200">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-gray-900">Overall RCA Score:</span>
                              <span className="text-2xl font-bold text-blue-600">
                                {hfPreview.rca_score?.toFixed(1)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-2">{hfPreview.assessment}</p>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={handleAddFromHuggingFace}
                          disabled={loading}
                          className="w-full px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                          {loading ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              Adding...
                            </>
                          ) : (
                            <>
                              ✨ Add to Dashboard
                            </>
                          )}
                        </button>
                      </>
                    )}
                  </div>
                )}

                {!hfPreview && (
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Manual Mode */}
            {mode === 'manual' && (
              <form onSubmit={handleSubmit}>
                <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-2">
                  {/* Basic Information */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                      📋 Basic Information
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Model Name *
                        </label>
                        <input
                          type="text"
                          required
                          value={formData.name}
                          onChange={(e) => handleInputChange('name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="e.g., GPT-4"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Provider *
                        </label>
                        <input
                          type="text"
                          required
                          value={formData.provider}
                          onChange={(e) => handleInputChange('provider', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="e.g., OpenAI"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Version *
                        </label>
                        <input
                          type="text"
                          required
                          value={formData.version}
                          onChange={(e) => handleInputChange('version', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="e.g., v1.0"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                      ⚙️ Model Metadata
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Parameters *
                        </label>
                        <input
                          type="text"
                          required
                          value={formData.metadata.parameters}
                          onChange={(e) => handleMetadataChange('parameters', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="e.g., 175B"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Context Window *
                        </label>
                        <input
                          type="number"
                          required
                          min="1"
                          value={formData.metadata.context_window || ''}
                          onChange={(e) => handleMetadataChange('context_window', parseInt(e.target.value) || 0)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="e.g., 8192"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Release Date *
                        </label>
                        <input
                          type="date"
                          required
                          value={formData.metadata.release_date}
                          onChange={(e) => handleMetadataChange('release_date', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Task Scores */}
                  <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-4">
                    <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                      📊 RCA Task Scores (0-100)
                    </h4>
                    <p className="text-sm text-gray-600 mb-4">
                      Rate the model's performance on each RCA task from 0 to 100
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {taskFields.map((field) => (
                        <div key={field.key} className="bg-white rounded-lg p-4 shadow-sm">
                          <label className="block text-sm font-medium text-gray-900 mb-1">
                            {field.label}
                          </label>
                          <p className="text-xs text-gray-500 mb-2">{field.description}</p>
                          <div className="flex items-center gap-3">
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={formData.task_scores[field.key]}
                              onChange={(e) => handleTaskScoreChange(field.key, parseInt(e.target.value))}
                              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                              style={{
                                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${formData.task_scores[field.key]}%, #e5e7eb ${formData.task_scores[field.key]}%, #e5e7eb 100%)`
                              }}
                            />
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={formData.task_scores[field.key]}
                              onChange={(e) => handleTaskScoreChange(field.key, Math.min(100, Math.max(0, parseInt(e.target.value) || 0)))}
                              className="w-16 px-2 py-1 text-center border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-6 flex items-center justify-between pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-500">
                    * Required fields | RCA score will be calculated automatically
                  </p>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={handleClose}
                      className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                      disabled={loading}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-6 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Adding...
                        </>
                      ) : (
                        <>
                          ✨ Add Model
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddModelModal;

// Made with Bob