# Invoice Agent Test Documentation

## Overview
This document provides an overview of the test suite for the Invoice Agent application, which performs OCR on invoice documents and extracts structured data using language models.

## Test Structure
The test suite is organized into the following directories:

- **test_api**: Tests for the API endpoints
- **test_services**: Tests for core service functionality
- **test_utils**: Tests for utility functions
- **fixtures**: Test data and fixtures

## Key Components Tested

### API Endpoints (test_api/test_invoices.py)
- **TestUploadEndpoint**: Tests the file upload functionality
  - Upload PDF documents
  - Upload PNG images
  - Reject unsupported file types

- **TestProcessEndpoint**: Tests the invoice processing endpoint
  - Process single invoice files
  - Handle non-existent files

- **TestResultsEndpoint**: Tests retrieving processing results
  - Get results for processed invoices
  - Handle non-existent results

- **TestCleanupEndpoint**: Tests the storage cleanup functionality
  - Clean up directories and files

### Services (test_services/)

#### OCR Service (test_ocr_service.py)
- **TestDocParser**: Tests the document parsing functionality
  - Parse PDF files (single-page)
  - Parse PDF files (multi-page)
  - Handle file not found errors

- **TestProcessInvoice**: Tests the invoice processing pipeline
  - Successfully process invoices
  - Handle missing files
  - Process without annotation

#### Annotator (test_annotator.py)
- **TestInvoiceAnnotator**: Tests the annotation functionality
  - Load and process PNG images
  - Load and process PDF documents
  - Find text locations in images
  - Match fields to text locations
  - Generate annotated images

#### Processing (test_processing.py)
- **TestValidateNetGross**: Tests validation of net and gross amounts
- **TestFilterVatIds**: Tests filtering of VAT IDs
- **TestFilterOrderIds**: Tests filtering of order IDs
- **TestUpdateImageUrls**: Tests updating image URLs with base URLs

### Utilities (test_utils/test_utils.py)
- **TestCleanAmount**: Tests cleaning of monetary amounts
- **TestFileExtension**: Tests file extension utilities
- **TestResponseUtils**: Tests API response utilities

## Test Configuration
- **conftest.py**: Defines test fixtures and mock configurations
- **pytest.ini**: Defines pytest configuration and test markers
- **test_config.py**: Provides test-specific configuration

## Test Fixtures
Test fixtures are created using the script `fixtures/create_test_fixtures.py`, which generates:
- Minimal PDF and PNG files for testing
- Sample extraction data in JSON format
- Multi-page extraction results
- Sample API responses

## Running Tests
Tests can be run using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test files
pytest tests/test_api/test_invoices.py

# Run specific test class
pytest tests/test_api/test_invoices.py::TestUploadEndpoint
```

## Mocking Strategy
The tests use extensive mocking to:
- Mock the language model for consistent results
- Isolate components for unit testing
- Simulate file operations without actual file I/O
- Mock HTTP responses for API testing