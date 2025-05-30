# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within AWS Inventory Scanner, please follow these steps:

1. **Do not disclose the vulnerability publicly** until it has been addressed by the maintainers.

2. **Email the maintainers** directly with details of the vulnerability. Please include:
   - A description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact of the vulnerability
   - Any suggested fixes or mitigations (if you have them)

3. **Allow time for response**. The maintainers will acknowledge your report within 48 hours and will work to address the issue as quickly as possible.

4. Once the vulnerability has been addressed, the maintainers will coordinate with you on the disclosure timeline.

## Security Best Practices

When using AWS Inventory Scanner, please follow these security best practices:

1. **Use least-privilege IAM roles** when running the scanner. The tool only needs read-only permissions to the AWS services you want to scan.

2. **Do not commit AWS credentials** to version control systems.

3. **Review the output files** before sharing them, as they may contain sensitive information about your AWS infrastructure.

4. **Keep the tool updated** to the latest version to benefit from security fixes.

## Security Features

AWS Inventory Scanner includes the following security features:

1. **No persistent storage** of AWS credentials - the tool uses the AWS SDK's standard credential providers.

2. **No external API calls** outside of AWS services.

3. **Open source code** that can be audited for security issues.

## Dependencies

We regularly monitor and update dependencies to address security vulnerabilities. If you discover a vulnerability in a dependency, please report it following the process above.
