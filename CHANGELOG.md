# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for base64 encoded Google Sheets credentials
- Comprehensive development documentation
- New test fixtures for mocking credentials and clients

### Changed
- Improved error handling in ShaunAgent class
- Enhanced cleanup functionality for both success and error cases
- Updated test suite to use standardized mock credentials
- Refactored Google Sheets client initialization process

### Fixed
- Test failures related to mock credentials
- Resource cleanup in error cases
- Proper handling of None clients during cleanup
- Base64 credential decoding edge cases

## [3.0.0] - 2024-02-08

### Added
- Initial release of Zigral 3.0
- Virtual Desktop Infrastructure (VDI) support
- Integration with Google Sheets
- RabbitMQ messaging system
- Automated test suite 