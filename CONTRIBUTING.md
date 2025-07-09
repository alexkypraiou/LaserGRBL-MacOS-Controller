# Contributing to LaserGRBL-MacOS-Controller

Thank you for your interest in contributing to the LaserGRBL-MacOS-Controller project! We welcome contributions from the community to help make this tool better for everyone.

## How to Contribute

### Reporting Issues

If you encounter bugs or have feature requests:

1. **Search existing issues** first to avoid duplicates
2. **Use the issue templates** if available
3. **Provide detailed information** including:
   - Operating system version
   - Python version
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots if applicable

### Submitting Code Changes

1. **Fork the repository** to your GitHub account
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the coding standards below
4. **Test your changes** thoroughly
5. **Submit a pull request** with a clear description of your changes

## Development Setup

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/LaserGRBL-MacOS-Controller.git
   cd LaserGRBL-MacOS-Controller
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application to test:**
   ```bash
   python LaserGRBLMacOS.py
   ```

## Coding Standards

- **Follow PEP 8** Python style guidelines
- **Write clear, descriptive variable and function names**
- **Add docstrings** to all functions and classes
- **Comment complex logic** for clarity
- **Keep functions focused** on a single responsibility
- **Handle errors gracefully** with appropriate error messages

## Testing

- Test your changes thoroughly before submitting
- If adding new features, consider adding unit tests
- Ensure the application runs without errors
- Test on different screen sizes and resolutions when applicable

## Documentation

When making changes:
- Update the README.md if your changes affect usage
- Add inline comments for complex code
- Update docstrings for modified functions

## Code Review Process

All submissions require review. We use GitHub pull requests for this process:

1. Submit your pull request
2. Wait for review from maintainers
3. Address any feedback or requested changes
4. Once approved, your changes will be merged

## Questions?

If you have questions about contributing:
- Open an issue with the "question" label
- Check existing issues and discussions

## License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

Thank you for contributing!