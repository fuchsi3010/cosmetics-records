# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Cosmetics Records seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do

- **Report vulnerabilities privately** - Do not create public GitHub issues for security vulnerabilities
- **Provide details** - Include steps to reproduce, potential impact, and any suggested fixes
- **Allow time for response** - Give us reasonable time to respond before any disclosure

### Please Do Not

- **Do not disclose publicly** - Avoid posting vulnerability details in public issues, discussions, or social media until we have addressed it
- **Do not exploit vulnerabilities** - Only test against your own installations
- **Do not access other users' data** - Even if a vulnerability would allow it

### How to Report

**Email**: Report security vulnerabilities by creating a private security advisory on GitHub:

1. Go to the repository's Security tab
2. Click "Report a vulnerability"
3. Fill out the form with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

Alternatively, you can email security concerns to the repository maintainer.

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt within 48 hours
2. **Assessment**: We will assess the vulnerability and its impact
3. **Updates**: We will keep you informed of our progress
4. **Resolution**: We aim to resolve critical issues within 7 days
5. **Credit**: We will credit you in the release notes (unless you prefer to remain anonymous)

## Security Measures

Cosmetics Records implements several security measures:

### Data Protection

- **SQL Injection Prevention**: All database queries use parameterized statements
- **Input Validation**: Pydantic models validate all user input
- **Path Traversal Protection**: File operations validate paths are within expected directories

### Local Data Security

- **Local Storage**: All data is stored locally on your machine
- **No Cloud Transmission**: No data is sent to external servers
- **Database Location**: SQLite database in user's application data directory
- **Backup Encryption**: Backups are ZIP files (consider encrypting sensitive backups externally)

### Application Security

- **No Network Access**: The application does not require internet connectivity
- **No External Dependencies at Runtime**: All functionality works offline
- **Foreign Key Constraints**: Database enforces referential integrity

## Security Best Practices for Users

1. **Regular Backups**: Enable automatic backups and store copies in secure locations
2. **File Permissions**: Ensure your application data directory has appropriate permissions
3. **System Updates**: Keep your operating system and Python environment updated
4. **Sensitive Data**: Be mindful of what client information you store

## Scope

This security policy applies to the Cosmetics Records application codebase. Third-party dependencies have their own security policies.

## Updates

This security policy may be updated from time to time. Please check back periodically for any changes.
