# Contributing to Arjun

Thank you for your interest in contributing to Arjun! We welcome contributions from everyone. This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and adhere to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inspiring community for all.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots and animated GIFs if possible**
- **Include your environment details**:
  - OS and version
  - Python version
  - Ollama version
  - Model being used
  - Streamlit version

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and expected behavior**
- **Explain why this enhancement would be useful**

### 📝 Pull Requests

- Fill in the required template
- Follow the Python styleguides
- Include appropriate test cases
- End all files with a newline
- Avoid platform-dependent code

## Development Setup

### Prerequisites
- Python 3.9+
- Git
- Ollama

### Steps

1. **Fork the repository**
   ```bash
   # Navigate to https://github.com/suyash-salvi/arjun-reviewer/fork
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/arjun-reviewer.git
   cd arjun-reviewer
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/descriptive-branch-name
   ```

6. **Make your changes**
   - Write clean, readable code
   - Add comments for complex logic
   - Update documentation if needed

7. **Test your changes**
   ```bash
   # Run the application
   streamlit run app.py
   
   # Test manually with various file types and models
   ```

8. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add meaningful commit message"
   ```

9. **Push to your fork**
   ```bash
   git push origin feature/descriptive-branch-name
   ```

10. **Create a Pull Request**
    - Navigate to the repository on GitHub
    - Click "New Pull Request"
    - Select your feature branch
    - Fill in the PR template with details

## Styleguides

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Use meaningful variable and function names
- Maximum line length: 100 characters
- Use docstrings for functions and classes

Example:
```python
def calculate_issue_hash(issue_data: dict) -> str:
    """
    Calculate SHA-256 hash of issue data for deduplication.
    
    Args:
        issue_data: Dictionary containing issue details
        
    Returns:
        str: SHA-256 hash of the issue
    """
    import hashlib
    issue_string = str(sorted(issue_data.items()))
    return hashlib.sha256(issue_string.encode()).hexdigest()
```

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add database connection pooling for improved performance

This implements connection pooling to reduce overhead when
scanning multiple files. Improves performance by ~30% in
batch operations.

Fixes #123
```

### Documentation

- Use clear and concise language
- Include code examples where applicable
- Keep documentation synchronized with code changes
- Use Markdown formatting for consistency

## Areas for Contribution

### High Priority
- [ ] Docker support and Dockerfile
- [ ] Unit tests and integration tests
- [ ] Performance optimizations
- [ ] Bug fixes from open issues

### Medium Priority
- [ ] API endpoints for CI/CD integration
- [ ] Custom prompt templates
- [ ] Batch file processing
- [ ] Export functionality (PDF, JSON)

### Low Priority
- [ ] UI/UX improvements
- [ ] Additional theme support
- [ ] Documentation improvements
- [ ] Example code and tutorials

## Recognition

Contributors will be:
- Added to the CONTRIBUTORS.md file
- Mentioned in release notes
- Credited in documentation

## Questions or Need Help?

- Open a [GitHub Discussion](https://github.com/suyash-salvi/arjun-reviewer/discussions)
- Check existing [Issues](https://github.com/suyash-salvi/arjun-reviewer/issues)
- Review the [README](README.md) and documentation

## License

By contributing to Arjun, you agree that your contributions will be licensed under its MIT License.

---

Thank you for contributing to make Arjun better! 🎉
