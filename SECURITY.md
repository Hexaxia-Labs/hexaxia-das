# Security Policy

## Supported Versions

Hexaxia DAS is at an early stage (v0.4.0, POC). Security fixes are applied to the
latest release only.

| Version | Supported |
|---------|-----------|
| 0.4.x   | Yes       |
| < 0.4   | No        |

## Reporting a Vulnerability

Please report security issues privately rather than opening a public issue.

- Email: security@hexaxia.tech
- Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  on this repository if enabled.

Include a description of the issue, steps to reproduce, and the affected version.
We aim to acknowledge reports within 5 business days.

## Scope

Hexaxia DAS is a filesystem-layout convention and CLI. It has no network surface,
no authentication, and no access-control model - permissions are whatever the host
filesystem, repository, or downstream system provides. The most relevant classes of
issue are: path handling in the validator and file creator, YAML loading of config
and manifest files, and any code path that writes to disk based on user input.
