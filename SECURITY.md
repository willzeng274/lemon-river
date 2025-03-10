# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Lemon River, please report it by creating a new issue with the title "Security Vulnerability" and mark it as confidential. We take all security bugs seriously, especially given the sensitive nature of job application data.

## Security Considerations

### Data Privacy
- All job application data is stored locally in SQLite database files
- No data is transmitted to external servers except:
  - Voice data processed through local MLX Whisper
  - Commands processed through local Ollama server
- Resume files remain on your local system
- Clipboard data is only processed when explicitly commanded

### System Access
- The application requires specific system permissions (detailed in README.md)
- These permissions are necessary for core functionality:
  - Microphone access for voice commands
  - Input monitoring for clipboard access
  - Full disk access for resume management
  - Accessibility for UI interactions

### Known Limitations
1. Voice data is temporarily stored as .wav files before processing
2. Clipboard content is held in memory during processing
3. No encryption for local database (relies on system-level security)

## Best Practices for Users

1. Keep your system updated
2. Don't run the application with elevated privileges
3. Regularly clean the recordings directory
4. Be mindful of clipboard content when using voice commands
5. Don't store sensitive credentials in resume files

## Version Support

We only support the latest version of Lemon River. Please ensure you're running the most recent release.

## Security Updates

Security updates will be released as needed. Users should:
1. Watch the repository for security announcements
2. Update to the latest version when security patches are released
3. Check the commit history for security-related changes

## Development Guidelines

When contributing, please:
1. Never commit sensitive data or credentials
2. Use secure coding practices
3. Validate user input
4. Handle errors gracefully
5. Document security implications of new features

## Threat Model

### Protected Assets
- Job application details
- Resume content
- Voice recordings
- Clipboard data during processing

### Trust Boundaries
- Local system security
- Python environment integrity
- Ollama server security
- MLX Whisper processing

### Potential Risks
1. Unauthorized system access
2. Clipboard data exposure
3. Voice command spoofing
4. Resume template injection

## Acknowledgments

We appreciate security researchers and users reporting vulnerabilities. All valid reports will be acknowledged in our release notes.