# MongoDB Index Performance Test Tool

## Overview

The MongoDB Index Performance Test is a tool designed to evaluate the performance of various index configurations on MongoDB queries. This project allows users to test different index hints and measure the performance metrics, such as average execution time, minimum and maximum execution times, standard deviation, and the number of documents and keys examined.

## Features

- Connect to a MongoDB database and perform index performance tests.
- Support for multiple output formats: table, CSV, and JSON.
- Configurable warm-up iterations and sample intervals.
- Detailed logging of test results and errors.
- Ability to clear the query plan cache before testing.

## Requirements

- Python 3.7 or higher
- MongoDB server

You can install the required packages using pip:
```bash
pip install -r requirements.txt
```

## Usage

To run the performance tests, use the following command:

```bash
python src/run.py --test-config query_example.json
```

### Options

- `--connection`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `--iterations`: Number of iterations for the performance test (default: 1000)
- `--warmup`: Number of warm-up iterations (default: 10)
- `--sample-interval`: Sample interval for collecting execution statistics (default: 1)
- `--output-format`: Format for outputting results (`table`, `csv`, `json`, default: `table`)
- `--output-dir`: Directory to save the output results (default: current directory)

## Test Configuration

The test configuration should be provided in a JSON file format. Here is an example of the configuration structure:

```json
[
    {
        "name": "test_query_1",
        "database": "my_database",
        "collection": "users",
        "query": {
            "filter": {
                "name": "John Doe",
                "age": {
                    "$gte": 30
                }
            },
            "sort": {
                "age": -1
            },
            "project": {
                "name": 1,
                "age": 1
            }
        },
        "hints": [
            {
                "name": 1
            },
            {
                "age": 1
            }
        ]
    }
]
```

Each test query object should contain:
- `name`: Unique identifier for the test
- `database`: Target database name
- `collection`: Target collection name
- `query`: MongoDB query document
- `hints`: Array of index hints to test

### Output Example

The tool will output performance statistics in your chosen format. Example table output:

```
+-------------+------------+------------------+----------------+---------------+---------------+---------------+------------+---------+---------+----------+----------+--------------+
| Index Hint  | Iteration  | Warmup Iteration | Sample Interval| Avg Time (s)  | Min Time (s)  | Max Time (s)  | StdDev     | 95th %  | 99th %  | Avg Docs | Avg Keys | Avg Returned |
+-------------+------------+------------------+----------------+---------------+---------------+---------------+------------+---------+---------+----------+----------+--------------+
| {"field1":1}| 1000       | 10               | 1              | 0.000123      | 0.000098      | 0.000189      | 0.000023   | 0.000156| 0.000178| 1.0      | 1.0      | 1.0          |
+-------------+------------+------------------+----------------+---------------+---------------+---------------+------------+---------+---------+----------+----------+--------------+
```

### To Do
- Add support for parallel testing