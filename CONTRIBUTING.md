# Contributing to LaserGRBL-MacOS-Controller

Thank you for your interest in contributing to LaserGRBL-MacOS-Controller! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PyQt6
- Pillow (PIL)
- macOS (for full testing, though development can be done on other platforms)

### Installation

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/LaserGRBL-MacOS-Controller.git
   cd LaserGRBL-MacOS-Controller
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Test the application:
   ```bash
   python3 LaserGRBLMacOS.py
   ```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (Python version, PyQt6 version, macOS version)
- **Error messages** or logs if applicable
- **Screenshots** for UI-related issues

### Suggesting Features

Feature requests are welcome! Please provide:

- **Clear description** of the proposed feature
- **Use case** explaining why this feature would be useful
- **Implementation ideas** if you have any

### Code Contributions

1. **Fork and branch**: Create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow coding standards**:
   - Use meaningful variable and function names
   - Add comments for complex logic
   - Follow PEP 8 style guidelines
   - Keep functions focused and modular

3. **Test your changes**:
   - Test the application manually
   - Run existing tests if available: `pytest`
   - Add tests for new functionality

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots for UI changes

## Code Style Guidelines

- **Python**: Follow PEP 8
- **Comments**: Use clear, concise comments for complex logic
- **Error handling**: Implement proper error handling with user-friendly messages
- **UI**: Maintain consistency with the existing dark theme design

## Areas for Contribution

- **Serial communication improvements**
- **G-code processing enhancements**
- **UI/UX improvements**
- **Image processing optimizations**
- **Error handling and user feedback**
- **Documentation improvements**
- **Testing and quality assurance**

## Testing

When contributing code:

1. Test the application with actual hardware if possible
2. Test error conditions and edge cases
3. Verify UI responsiveness and usability
4. Test on different screen sizes and resolutions

## Questions?

If you have questions about contributing, feel free to:

- Open an issue with the "question" label
- Check existing issues and discussions
- Contact the maintainers

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

Thank you for contributing to LaserGRBL-MacOS-Controller!