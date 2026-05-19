# 🎯 Arjun - Code Review Automation Tool

**Arjun** (symbolizing precision and focus) is an AI-powered code review automation tool that leverages local LLMs through Ollama for comprehensive code analysis.

## Features

### Core Capabilities
- **Automated Code Review**: Upload code files and get instant AI-powered reviews
- **Persistent Storage**: SQLite database stores all review outputs for reuse and tracking
- **Smart Issue Tracking**: Hash-based issue identification prevents duplicates
- **Three-Section Issue Display**:
  1. **New Issues**: First-time detected issues with severity, line number, type, description, and solution
  2. **Existing Issues**: Previously detected but unresolved issues
  3. **Resolved Issues**: Issues that have been fixed based on LLM comparison

### Additional Features
- **User Acceptance Ratio**: Track how many issues users have acknowledged/addressed
- **Multi-Language Support**: Supports Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, and more
- **LLM Optimization**: Persistent storage reduces redundant LLM calls

## Tech Stack

- **LangChain**: LLM orchestration and prompt management
- **Ollama**: Local LLM inference (DeepSeek, CodeLlama, etc.)
- **SQLite**: Lightweight, persistent storage
- **Streamlit**: Modern, interactive web UI

## Prerequisites

1. **Python 3.9+** installed
2. **Ollama** installed and running ([Install Ollama](https://ollama.ai/))
3. **DeepSeek Coder** model (or your preferred coding model)

## Installation

### 1. Clone/Navigate to the Project
```bash
cd arjun-reviewer
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama Model
```bash
# Install DeepSeek Coder (recommended)
ollama pull deepseek-coder:6.7b

# Or smaller variant
ollama pull deepseek-coder:1.3b

# Or CodeLlama alternative
ollama pull codellama:7b
```

### 5. Start Ollama Server
```bash
ollama serve
```

## Usage

### Running the Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### How to Use

1. **Configure Model**: Select your Ollama model in the sidebar
2. **Check Connection**: Click "Check Ollama Connection" to verify setup
3. **Upload File**: Click the upload button and select a code file
4. **Review Code**: Click "Review Code with Arjun" to start analysis
5. **View Results**: Browse through New, Existing, and Resolved issues tabs
6. **Acknowledge Issues**: Mark issues as acknowledged to track acceptance

## Project Structure

```
arjun-reviewer/
├── app.py                 # Streamlit UI application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── core/
│   ├── __init__.py
│   └── reviewer.py       # Main review orchestration logic
├── database/
│   ├── __init__.py
│   └── db_manager.py     # SQLite database operations
├── llm/
│   ├── __init__.py
│   └── reviewer.py       # LangChain + Ollama integration
└── arjun_reviews.db      # SQLite database (created on first run)
```

## Database Schema

### Files Table
- Tracks uploaded files with hash-based identification
- Records scan count and timestamps

### Issues Table
- Stores all detected issues with unique hash
- Tracks severity, line number, type, description, solution
- Status (open/resolved) and user acknowledgment

### Scan History Table
- Records each scan with issue counts
- Enables analytics and progress tracking

## Configuration Options

### Supported LLM Models
- `deepseek-coder:6.7b` (Recommended)
- `deepseek-coder:1.3b` (Faster, less accurate)
- `codellama:7b`
- `codellama:13b`
- `llama2:7b`
- `mistral:7b`

### Supported File Types
Python, JavaScript, TypeScript, JSX, TSX, Java, C, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, SQL, Shell

## Issue Severity Levels

| Level | Color | Description |
|-------|-------|-------------|
| 🔴 Critical | Red | Security vulnerabilities, crashes |
| 🟠 High | Orange | Bugs, significant issues |
| 🟡 Medium | Yellow | Code quality, performance |
| 🟢 Low | Green | Style, minor improvements |

## Metrics Explained

- **Acceptance Rate**: Percentage of open issues acknowledged by user
- **Resolution Rate**: Percentage of total issues that have been resolved
- **Scan Count**: Number of times a file has been reviewed

## Troubleshooting

### Ollama Connection Failed
```bash
# Ensure Ollama is running
ollama serve

# Check if model is installed
ollama list
```

### Model Not Found
```bash
# Pull the required model
ollama pull deepseek-coder:6.7b
```

### Slow Performance
- Use a smaller model variant (e.g., `deepseek-coder:1.3b`)
- Ensure adequate RAM (8GB+ recommended)
- Consider GPU acceleration if available

## License

MIT License - Feel free to use and modify for your needs.

## Contributing

Contributions welcome! Please submit issues and pull requests.

---

**Built with ❤️ for developers who value code quality**
