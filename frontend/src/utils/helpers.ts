/**
 * Utility functions for the RCA Dashboard
 */

export const getRatingColor = (score: number): string => {
  if (score >= 90) return 'text-green-600 bg-green-50';
  if (score >= 80) return 'text-lime-600 bg-lime-50';
  if (score >= 70) return 'text-yellow-600 bg-yellow-50';
  if (score >= 60) return 'text-orange-600 bg-orange-50';
  return 'text-red-600 bg-red-50';
};

export const getRatingLabel = (score: number): string => {
  if (score >= 90) return 'Excellent for RCA';
  if (score >= 80) return 'Very Good for RCA';
  if (score >= 70) return 'Good for RCA';
  if (score >= 60) return 'Fair for RCA';
  return 'Not Recommended for RCA';
};

export const getRatingBadgeColor = (score: number): string => {
  if (score >= 90) return 'bg-green-500';
  if (score >= 80) return 'bg-lime-500';
  if (score >= 70) return 'bg-yellow-500';
  if (score >= 60) return 'bg-orange-500';
  return 'bg-red-500';
};

export const formatTaskName = (taskId: string): string => {
  return taskId
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

export const getMedalEmoji = (rank: number): string => {
  switch (rank) {
    case 1: return '🥇';
    case 2: return '🥈';
    case 3: return '🥉';
    default: return '';
  }
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

export const getProgressBarColor = (score: number): string => {
  if (score >= 90) return 'bg-green-500';
  if (score >= 80) return 'bg-lime-500';
  if (score >= 70) return 'bg-yellow-500';
  if (score >= 60) return 'bg-orange-500';
  return 'bg-red-500';
};

// Made with Bob
