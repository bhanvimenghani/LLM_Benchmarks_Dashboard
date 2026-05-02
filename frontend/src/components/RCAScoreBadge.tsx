import React from 'react';
import { getRatingBadgeColor, getRatingLabel } from '../utils/helpers';

interface RCAScoreBadgeProps {
  score: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

const RCAScoreBadge: React.FC<RCAScoreBadgeProps> = ({ 
  score, 
  size = 'medium',
  showLabel = true 
}) => {
  const sizeClasses = {
    small: 'w-12 h-12 text-sm',
    medium: 'w-16 h-16 text-xl',
    large: 'w-32 h-32 text-4xl'
  };

  const labelSizeClasses = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  return (
    <div className="flex items-center gap-3">
      <div
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center text-white font-bold shadow-md ${getRatingBadgeColor(score)}`}
      >
        <div className="flex flex-col items-center leading-tight">
          <span>{score}</span>
          <span className="text-xs opacity-90">/100</span>
        </div>
      </div>
      {showLabel && (
        <span className={`${labelSizeClasses[size]} font-semibold text-gray-700`}>
          {getRatingLabel(score)}
        </span>
      )}
    </div>
  );
};

export default RCAScoreBadge;

// Made with Bob
