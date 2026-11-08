# Security Policy

## Historical Book AI Translator

Thank you for helping keep Historical Book AI Translator safe and secure.

This is an open-source project focused on preserving historical knowledge through AI-assisted transcription, translation, and future historically grounded AI agents.

Security matters because the project uses Python, local AI inference through AMD Lemonade, and optional external AI services.

## Supported Versions

The project is currently in active prototype development.

| Version | Security Support |
|---|---|
| Latest version on the main branch | Supported |
| Older versions | Not officially supported |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately.

**Preferred method:** Use GitHub's private vulnerability reporting feature if enabled for this repository.

If private reporting is unavailable, open a GitHub Discussion requesting a private contact method. Do not include sensitive exploit details, credentials, or private information in public posts.

Please include:

- A description of the vulnerability.
- Steps to reproduce the issue.
- The affected files or components.
- The potential security impact.
- Suggested fixes, if available.

Reports will be reviewed as time permits. No guaranteed response or resolution timeline is currently offered.

## API Keys and Sensitive Information

Never commit API keys, passwords, access tokens, or other private credentials to this repository.

Use environment variables for external service credentials.

Local development files may contain private settings and should be reviewed before publication.

## Local AI and External Services

Historical Book AI Translator supports local AI processing through AMD Lemonade and optional cloud-based AI services.

Users should verify their selected backend and understand that cloud processing may transmit document content to an external provider.

Only connect the local API server to trusted applications and networks.

## Responsible Development

Contributors are encouraged to report security concerns, review dependencies, avoid exposing private information, and help improve the reliability of the project.

As the project expands into historical AI agents, additional languages, and potentially VR environments, security practices will evolve alongside its capabilities.

## Project Philosophy

Preserving history should not come at the cost of compromising the security or privacy of the people helping preserve it.

Our goal is to build something open, useful, historically responsible, and secure.
