import React from 'react';
import type { Category } from '../types';

interface CategorySelectorProps {
  categories: Record<string, Category>;
  activeCategory: string;
  onCategoryChange: (categoryId: string) => void;
}

const CategorySelector: React.FC<CategorySelectorProps> = ({
  categories,
  activeCategory,
  onCategoryChange,
}) => {
  const categoryOrder = ['rca', 'general', 'coding', 'reasoning'];
  const orderedCategories = categoryOrder
    .map(id => categories[id])
    .filter(Boolean);

  return (
    <div className="bg-white rounded-xl shadow-lg p-2 mb-6">
      <div className="flex gap-2 overflow-x-auto">
        {orderedCategories.map((category) => {
          const isActive = category.id === activeCategory;
          return (
            <button
              key={category.id}
              onClick={() => onCategoryChange(category.id)}
              className={`
                flex-1 min-w-[200px] px-6 py-4 rounded-lg font-medium transition-all
                ${isActive
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg scale-105'
                  : 'bg-gray-50 text-gray-700 hover:bg-gray-100 hover:shadow-md'
                }
              `}
            >
              <div className="flex flex-col items-center gap-2">
                <span className="text-3xl">{category.icon}</span>
                <span className="text-lg font-bold">{category.name}</span>
                <span className={`text-xs ${isActive ? 'text-blue-100' : 'text-gray-500'}`}>
                  {category.description.split(' ').slice(0, 4).join(' ')}...
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default CategorySelector;

// Made with Bob
