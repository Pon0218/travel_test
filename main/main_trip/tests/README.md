# Test Documentation

This documentation explains the various test files and how to run them.

## Test Files Overview

1. **`test_trip_planning.py`**
   - Tests the trip planning system functionality
   - Validates location and requirement handling

2. **`test_sql_search.py`**
   - Tests the CSV data search functionality
   - Validates condition-based filtering

3. **`test_qdrant_search.py`**
   - Tests vector search capabilities
   - Includes environment variable validation

4. **`test_search_performance.py`**
   - Compares single vs parallel search performance
   - Validates search result quality

5. **`test_llm.py`**
   - Tests LLM integration
   - Validates API response and thinking function

## Prerequisites

1. Install required packages:
```bash
pip install pytest python-dotenv
```
or
```bash
poetry add pytest python-dotenv
```

2. Set up environment variables in `.env` file:
```env
jina_url=your_jina_url
jina_headers_Authorization=your_authorization
qdrant_url=your_qdrant_url
qdrant_api_key=your_api_key
ChatGPT_api_key=your_chatgpt_api_key
```

## Running Tests

### Run all tests:
```bash
pytest -v main/main_trip/tests/
```

### Run specific test files:
```bash
# Run trip planning tests
pytest -v tests/test_trip_planning.py

# Run SQL search tests
pytest -v tests/test_sql_search.py

# Run Qdrant search tests
pytest -v tests/test_qdrant_search.py

# Run search performance tests with output
pytest -v -s tests/test_search_performance.py

# Run LLM tests
pytest -v tests/test_llm.py
```

### Additional test options:
```bash
# Run tests with detailed output
pytest -v -s tests/

# Run specific test function
pytest tests/test_file.py::test_function_name

# Run tests and show coverage
pytest --cov=feature tests/
```

## Test Result Interpretation

- `PASSED` (`.`): Test passed successfully
- `FAILED` (`F`): Test failed
- `ERROR` (`E`): Error occurred during test execution

Example successful output:
```
============================= test session starts ==============================
collected X items

test_file.py::test_function PASSED                                    [100%]

============================== X passed in Xs ===============================
```

## Common Issues & Solutions

1. **Environment Variable Errors**
   - Ensure all required variables are set in `.env`
   - Check variable names match exactly (case sensitive)

2. **API Response Timeout**
   - Default timeout is 30 seconds
   - Adjust timeout in test_api_response_time if needed

3. **Import Errors**
   - Verify project structure
   - Check Python path settings

## Adding New Tests

When adding new tests:
1. Create test file in `tests/` directory
2. Use appropriate fixtures from existing tests
3. Follow the pytest naming convention (`test_*.py`)
4. Include appropriate assertions and error handling

## Maintenance

- Keep test files organized by functionality
- Update test cases when API or functionality changes
- Maintain environment variable documentation
- Regular review and cleanup of test cases

For more details about specific test implementations, check the comments in individual test files.