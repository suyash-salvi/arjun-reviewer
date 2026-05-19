# 🎯 Arjun - Code Review Automation Tool

[![GitHub license](https://img.shields.io/github/license/suyash-salvi/arjun-reviewer)](https://github.com/suyash-salvi/arjun-reviewer/blob/main/LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28.0%2B-red)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/langchain-0.1.0%2B-green)](https://python.langchain.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Arjun** (symbolizing precision and focus) is an AI-powered code review automation tool that leverages local LLMs through Ollama for comprehensive code analysis. No cloud, no API keys—just intelligent, local code reviews powered by open-source models.

## ✨ Features

### 🔍 Core Capabilities
- **Automated Code Review**: Upload code files and get instant AI-powered reviews
- **Persistent Storage**: SQLite database stores all review outputs for reuse and tracking
- **Smart Issue Tracking**: Hash-based issue identification prevents duplicates
- **Three-Section Issue Display**:
  - **New Issues**: First-time detected issues with severity, line number, type, description, and solution
  - **Existing Issues**: Previously detected but unresolved issues
  - **Resolved Issues**: Issues that have been fixed based on LLM comparison

### 🚀 Additional Features
- **User Acceptance Ratio**: Track how many issues users have acknowledged/addressed
- **Multi-Language Support**: Supports Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, and more
- **LLM Optimization**: Persistent storage reduces redundant LLM calls
- **Privacy First**: All processing happens locally—no data leaves your machine
- **Model Flexibility**: Works with any Ollama-supported model

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM Orchestration** | [LangChain](https://python.langchain.com/) |
| **Local LLM Runtime** | [Ollama](https://ollama.ai/) |
| **Database** | SQLite |
| **Web Framework** | [Streamlit](https://streamlit.io/) |
| **Language** | Python 3.9+ |

## 📋 Prerequisites

- **Python 3.9** or higher
- **Ollama** installed and running ([Install Ollama](https://ollama.ai/))
- **DeepSeek Coder** model or preferred coding LLM
- **4GB+ RAM** (8GB+ recommended)

## 📥 Installation

### Quick Start (macOS/Linux)

```bash
# Clone the repository
git clone https://github.com/suyash-salvi/arjun-reviewer.git
cd arjun-reviewer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull an Ollama model
ollama pull deepseek-coder:6.7b

# In another terminal, start Ollama server
ollama serve

# Run the application (in the first terminal)
streamlit run app.py
```

The application will open at `http://localhost:8501`

### Windows Users

```powershell
git clone https://github.com/suyash-salvi/arjun-reviewer.git
cd arjun-reviewer

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

# Start Ollama (if not already running)
ollama serve

# In another PowerShell window
streamlit run app.py
```

### Docker Support (Coming Soon)

We're working on Docker support for easier deployment. Check back soon!

## 🚀 Usage

### Running the Application
```bash
streamlit run app.py
```

### Step-by-Step Guide

1. **Configure Model**: Select your Ollama model from the sidebar dropdown
2. **Verify Connection**: Click "Check Ollama Connection" to test the setup
3. **Upload Code File**: Select a code file to review
4. **Run Analysis**: Click "Review Code with Arjun" to start the review
5. **Review Results**: 
   - View new issues detected for the first time
   - Check existing unresolved issues
   - See resolved issues
6. **Track Progress**: Mark issues as acknowledged to track your acceptance ratio

### Supported File Types

Python, JavaScript, TypeScript, JSX, TSX, Java, C, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, SQL, Shell Script

## 📸 Screenshots

### 1. Upload File Interface
Upload your code files for analysis
![Upload File](assets/screenshots/Arjun:%20Upload%20File.png)

### 2. Preview Uploaded File
Preview the file content before analysis
![Preview File](assets/screenshots/Arjun:%20Preview%20uploaded%20file.png)

### 3. View Previewed File
Detailed view of the uploaded file
![View Previewed File](assets/screenshots/Arjun:%20View%20previewed%20file.png)

### 4. Analyze Code
Start the code review analysis with Arjun
![Analyze Code](assets/screenshots/Arjun:%20Analyze%20code.png)

### 5. New Issues Detected
View newly detected issues with severity, line numbers, and solutions
![New Issues](assets/screenshots/Arjun:%20New%20Issues.png)

### 6. Existing Issues
Previously detected but unresolved issues on file upload
![Existing Issues](assets/screenshots/Arjun:%20Exisiting%20issues%20on%20file%20upload.png)

### 7. Empty Existing Issues
When no existing issues are found
![Empty Existing Issues](assets/screenshots/Arjun:%20Empty%20Existing%20Issues.png)

### 8. Persisted Global Stats
Track metrics across all scans
![Global Stats](assets/screenshots/Arjun:%20Persisted%20Global%20Stats.png)

### 9. Rescanning After Fixes
Re-analyze the file after applying suggested fixes
![Rescanning File](assets/screenshots/Arjun:%20Rescanning%20the%20file%20after%20fixes.png)

### 10. Updated Metrics After Rescan
Metrics updated with improved issue resolution rates
![Updated Metrics](assets/screenshots/Arjun:%20Rescans%20with%20updated%20metrics.png)

## 📁 Project Structure

```
arjun-reviewer/
├── app.py                      # Streamlit UI application
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT License
├── README.md                   # This file
├── CONTRIBUTING.md             # Contributing guidelines
├── CODE_OF_CONDUCT.md          # Community code of conduct
├── core/
│   ├── __init__.py
│   └── reviewer.py             # Main review orchestration logic
├── database/
│   ├── __init__.py
│   └── db_manager.py           # SQLite database operations
├── llm/
│   ├── __init__.py
│   └── reviewer.py             # LangChain + Ollama integration
└── arjun_reviews.db            # SQLite database (auto-created)
```

## 🗄️ Database Schema

### Files Table
- `id`: Primary key
- `file_hash`: SHA-256 hash of file content (prevents duplicates)
- `file_path`: Original file path
- `scan_count`: Number of times reviewed
- `created_at`: First scan timestamp
- `updated_at`: Last scan timestamp

### Issues Table
- `id`: Primary key
- `file_id`: Reference to Files table
- `issue_hash`: Unique hash of the issue (deduplication)
- `severity`: Critical, High, Medium, Low
- `line_number`: Code line where issue occurs
- `issue_type`: Category of issue
- `description`: Detailed problem description
- `solution`: Recommended fix
- `status`: open, acknowledged, resolved
- `created_at`: Detection timestamp

### Scan History Table
- `id`: Primary key
- `file_id`: Reference to Files table
- `new_issues_count`: Number of new issues found
- `existing_issues_count`: Previously detected issues
- `resolved_issues_count`: Fixed issues
- `scan_date`: Timestamp of scan

## ⚙️ Configuration

### Supported LLM Models

**Recommended:**
- `deepseek-coder:6.7b` - Best accuracy, balanced speed
- `deepseek-coder:1.3b` - Faster, suitable for basic reviews

**Alternatives:**
- `codellama:7b` - Specialized for code
- `codellama:13b` - More powerful variant
- `llama2:7b` - General purpose
- `mistral:7b` - Fast inference

```bash
# Install a model
ollama pull deepseek-coder:6.7b

# List installed models
ollama list

# Remove a model
ollama rm deepseek-coder:6.7b
```

### Issue Severity Levels

| Level | Icon | Description |
|-------|------|-------------|
| 🔴 Critical | 🔴 | Security vulnerabilities, crashes, data loss risks |
| 🟠 High | 🟠 | Bugs, significant issues, logic errors |
| 🟡 Medium | 🟡 | Code quality, performance, maintainability |
| 🟢 Low | 🟢 | Style, minor improvements, suggestions |

## 📊 Metrics Explained

- **Acceptance Rate**: `(Acknowledged Issues / Total Open Issues) × 100%`
- **Resolution Rate**: `(Resolved Issues / Total Issues Found) × 100%`
- **Scan Count**: Number of times a specific file has been reviewed

## 🛠️ Troubleshooting

### Ollama Connection Failed
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama server
ollama serve

# Check installed models
ollama list
```

### Model Not Found Error
```bash
# Pull the model
ollama pull deepseek-coder:6.7b

# Verify installation
ollama list
```

### Slow Performance
- Use a smaller model: `ollama pull deepseek-coder:1.3b`
- Ensure sufficient RAM (8GB+ recommended)
- Enable GPU acceleration if available
- Close other applications consuming resources

### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill the process (replace PID)
kill -9 <PID>
```

### Database Issues
```bash
# Backup existing database
mv arjun_reviews.db arjun_reviews.db.backup

# Application will create a new database on next run
streamlit run app.py
```

## 🤝 Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on:
- Code style and standards
- How to submit pull requests
- Reporting bugs
- Suggesting features

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/arjun-reviewer.git
cd arjun-reviewer

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
python -m pytest  # (when tests are added)

# Commit and push
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to:
- ✅ Use this commercially
- ✅ Modify the code
- ✅ Distribute it
- ✅ Use it privately

Conditions:
- Include a copy of the license and copyright notice

## 🌟 Roadmap

- [ ] Docker and Docker Compose support
- [ ] Web-based model selection and management
- [ ] Custom prompt templates
- [ ] Batch file processing
- [ ] API endpoint for CI/CD integration
- [ ] Performance metrics dashboard
- [ ] Multi-user support
- [ ] Review history export (PDF/JSON)
- [ ] Slack/Discord integration

## 📚 Learn More

- [Ollama Documentation](https://github.com/ollama/ollama)
- [LangChain Documentation](https://python.langchain.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [DeepSeek Coder Model](https://github.com/deepseek-ai/deepseek-coder)

## 💬 Community & Support

- **Issues**: [GitHub Issues](https://github.com/suyash-salvi/arjun-reviewer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/suyash-salvi/arjun-reviewer/discussions)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## 🙏 Acknowledgments

- Built with ❤️ for developers who value code quality
- Powered by open-source projects: Ollama, LangChain, and Streamlit
- Inspired by the need for privacy-first code review tools

## 📞 Contact & Connect

- **GitHub**: [@suyash-salvi](https://github.com/suyash-salvi)
- **Website**: [suyashsalvi.dorik.io](https://suyashsalvi.dorik.io)
- **Location**: Mumbai, India

---

**Give us a ⭐ if you find this project useful!**

Made with ❤️ for the open-source community
