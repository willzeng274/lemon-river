# Contributing to Lemon River

First off, thank you for considering contributing to Lemon River! It's people like you that make Lemon River such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please read the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

We foster an open and welcoming environment, and expect all participants to:
* Show respect and courtesy to others
* Use inclusive language
* Be supportive of different viewpoints
* Accept constructive criticism gracefully
* Focus on what's best for the community

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible
* Include your environment details (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed functionality
* Any possible drawbacks
* Screenshots or sketches if applicable

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the existing style
6. Issue that pull request!

## Development Process

1. Clone the repository
```bash
git clone https://github.com/yourusername/lemon-river.git
cd lemon-river
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. Create a branch
```bash
git checkout -b feature/your-feature-name
```

### Code Style

* Follow PEP 8 guidelines
* Use [Black](https://github.com/psf/black) for code formatting
* Write docstrings for all public methods
* Add type hints where possible
* Keep functions focused and modular

### Testing

* Write unit tests for new features
* Ensure all tests pass before submitting PR
* Run tests using:
```bash
pytest tests/
```

### Documentation

* Update the README.md if needed
* Document new features
* Keep docstrings up to date
* Add comments for complex logic

## Project Structure

```
lemon-river/
├── agent/              # AI and voice processing logic
├── db/                 # Database adapter and operations
├── gui/                # PyQt6 UI components
├── voice/              # Audio recording and transcription
├── tests/              # Test suite
└── docs/               # Documentation (TODO)
```

## Git Commit Messages

* Use these labels:
- ✨ feat: ...
- 🐛 fix: ...
- 📚 docs: ...
- 💄 style: ...
- ♻️ refactor: ...
- ✅ test: ...
- 🔨 chore: ...
* Reference issues and pull requests liberally after the first line in the description

## Additional Notes

### Issue and Pull Request Labels

* `bug`: Something isn't working
* `enhancement`: New feature or request
* `documentation`: Documentation only changes
* `good first issue`: Good for newcomers
* `help wanted`: Extra attention is needed
* `question`: Further information is requested

## Recognition

Contributors who make significant improvements will be added to the README.md acknowledgments section.

Thank you for contributing to Lemon River! 🍋