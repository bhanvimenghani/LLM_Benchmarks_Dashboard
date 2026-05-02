# 🎯 RCA Benchmarking Dashboard

A comprehensive web-based dashboard for evaluating Large Language Model (LLM) performance on Root Cause Analysis (RCA) tasks. This tool helps you compare models across multiple RCA-specific capabilities and identify the best model for your needs.

## 📋 Features

- **Task-Based Leaderboards**: View top-performing models for each RCA task
- **Overall RCA Scoring**: Weighted scoring system to rank models for RCA suitability
- **Interactive Dashboard**: Clean, responsive UI with real-time data visualization
- **8 RCA Task Categories**:
  - Code Understanding (15% weight)
  - Log Analysis (20% weight)
  - Metric Interpretation (15% weight)
  - Causal Reasoning (20% weight)
  - Pattern Recognition (10% weight)
  - Context Synthesis (10% weight)
  - Root Cause Identification (5% weight)
  - Solution Recommendation (5% weight)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React + TypeScript Frontend                            │
│  - Dashboard with task leaderboards                     │
│  - Model comparison views                               │
│  - RCA score visualization                              │
└─────────────────────────────────────────────────────────┘
                         ↕ REST API
┌─────────────────────────────────────────────────────────┐
│  Python FastAPI Backend                                 │
│  - API endpoints for model data                         │
│  - RCA score calculation                                │
│  - Data service layer                                   │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│  JSON Data Store                                        │
│  - Model benchmark scores                               │
│  - Task definitions                                     │
│  - Metadata                                             │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.9+ (for backend)
- **npm** or **yarn** (package manager)

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd benchmarks_dashboard
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### Running the Application

#### Start Backend Server

```bash
# From backend directory with venv activated
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

#### Start Frontend Development Server

```bash
# From frontend directory
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## 📊 RCA Scoring Methodology

### How RCA Scores are Calculated

The RCA suitability score is a weighted average of performance across 8 task categories:

```
RCA Score = Σ(task_score × task_weight)
```

### Task Weights Explained

| Task | Weight | Rationale |
|------|--------|-----------|
| **Log Analysis** | 20% | Critical for RCA - parsing error logs and stack traces |
| **Causal Reasoning** | 20% | Core RCA skill - determining cause-effect relationships |
| **Code Understanding** | 15% | Essential for understanding system architecture |
| **Metric Interpretation** | 15% | Analyzing telemetry data and identifying anomalies |
| **Pattern Recognition** | 10% | Identifying recurring issues across incidents |
| **Context Synthesis** | 10% | Combining information from multiple data sources |
| **Root Cause Identification** | 5% | Direct RCA capability assessment |
| **Solution Recommendation** | 5% | Providing actionable fixes |

### Rating Categories

- **90-100**: 🟢 Excellent for RCA
- **80-89**: 🟡 Very Good for RCA
- **70-79**: 🟡 Good for RCA
- **60-69**: 🟠 Fair for RCA
- **Below 60**: 🔴 Not Recommended for RCA

## 📁 Project Structure

```
benchmarks_dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── api/
│   │   │   └── routes.py           # API endpoint definitions
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic data models
│   │   └── services/
│   │       ├── data_service.py     # Data loading and processing
│   │       └── rca_calculator.py   # RCA score calculation logic
│   ├── data/
│   │   └── models_tasks.json       # Model benchmark data
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RCAScoreBadge.tsx   # RCA score display component
│   │   │   └── TaskCard.tsx        # Task leaderboard card
│   │   ├── pages/
│   │   │   └── Dashboard.tsx       # Main dashboard page
│   │   ├── services/
│   │   │   └── api.ts              # API client service
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript type definitions
│   │   ├── utils/
│   │   │   └── helpers.ts          # Utility functions
│   │   ├── styles/
│   │   │   └── index.css           # Global styles
│   │   ├── App.tsx                 # Root component
│   │   └── main.tsx                # Application entry point
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.ts              # Vite configuration
│   ├── tsconfig.json               # TypeScript configuration
│   └── tailwind.config.js          # Tailwind CSS configuration
│
└── README.md                       # This file
```

## 🔌 API Endpoints

### Models

- `GET /api/models` - Get all models (with optional filters)
  - Query params: `provider`, `min_rca_score`, `max_rca_score`
- `GET /api/models/{model_id}` - Get specific model details

### Tasks

- `GET /api/tasks` - Get all tasks with leaderboards
- `GET /api/tasks/{task_id}` - Get specific task leaderboard

### Leaderboard

- `GET /api/leaderboard` - Get overall RCA leaderboard
  - Query params: `ascending` (default: false)

### Utilities

- `GET /api/providers` - Get list of model providers
- `GET /api/health` - Health check endpoint

## 📝 Sample Data

The dashboard currently uses sample data for 5 popular LLM models:

1. **GPT-4** (OpenAI) - RCA Score: 88.4
2. **Claude-3-Opus** (Anthropic) - RCA Score: 89.1
3. **Gemini-Pro** (Google) - RCA Score: 85.2
4. **Llama-3-70B** (Meta) - RCA Score: 80.7
5. **Mistral-Large** (Mistral AI) - RCA Score: 78.3

### Adding Your Own Data

To add or update model data, edit `backend/data/models_tasks.json`:

```json
{
  "models": [
    {
      "id": "your-model-id",
      "name": "Your Model Name",
      "provider": "Provider Name",
      "version": "model-version",
      "task_scores": {
        "code_understanding": 85.0,
        "log_analysis": 88.0,
        "metric_interpretation": 82.0,
        "causal_reasoning": 87.0,
        "pattern_recognition": 84.0,
        "context_synthesis": 86.0,
        "root_cause_identification": 83.0,
        "solution_recommendation": 81.0
      },
      "rca_score": 85.2,
      "metadata": {
        "parameters": "70B",
        "context_window": 8192,
        "release_date": "2024-01-01"
      }
    }
  ]
}
```

The RCA score will be automatically calculated based on the task scores and weights.

## 🛠️ Development

### Backend Development

```bash
# Run with auto-reload
cd backend
uvicorn app.main:app --reload

# Run tests (if implemented)
pytest

# Format code
black app/
```

### Frontend Development

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 🚀 Deployment

### Backend Deployment

```bash
# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Deployment

```bash
# Build for production
npm run build

# The dist/ folder can be deployed to any static hosting service
# (Vercel, Netlify, AWS S3, etc.)
```

## 🔮 Future Enhancements

- [ ] Real-time benchmark data integration from external APIs
- [ ] Custom benchmark upload functionality
- [ ] Model version tracking and comparison
- [ ] User authentication and saved comparisons
- [ ] Export reports as PDF/CSV
- [ ] Advanced filtering and search
- [ ] Model performance trends over time
- [ ] In-house document evaluation system
- [ ] Mix of Agents (MOA) validation framework
- [ ] Database integration (PostgreSQL/MongoDB)

## 📄 License

[Add your license here]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

[Add your contact information here]

---

**Note**: The current implementation uses sample benchmark data for demonstration purposes. For production use, integrate with actual benchmark testing systems or manually update the data based on real evaluations.