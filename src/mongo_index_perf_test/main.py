import sys
import json
import time
import argparse
import os
from datetime import datetime
from typing import List
from bson import ObjectId

from .config import DEFAULT_CONFIG, logger
from .connection import MongoDBConnection
from .models import TestQuery, TestResult
from .tester import IndexPerformanceTester
from .formatters import TableFormatter, CSVFormatter, JSONFormatter

def json_object_hook(d):
    def adjsut_object_id(value):
        if isinstance(value, str) and value.startswith("ObjectId("):
            return ObjectId(value[value.index("(") + 2 : value.index(")") - 1])
        elif isinstance(value, dict):
            return {key: adjsut_object_id(val) for key, val in value.items()}
        elif isinstance(value, list):
            return [adjsut_object_id(val) for val in value]
        else:
            return value
    for key, value in d.items():
        d[key] = adjsut_object_id(value)
    return d

def load_test_queries(config_path: str) -> List[TestQuery]:
    """Load test queries from configuration file"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f, object_hook=json_object_hook)
        return [TestQuery.from_dict(query_data) for query_data in data]
    except Exception as e:
        logger.error(f"Failed to load test config: {e}")
        sys.exit(1)

def save_results(
    results: List[TestResult], output_format: str, output_dir: str, query_name: str
) -> str:
    """Save test results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = query_name
    if name == "":
        name = "index_performance_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_filename = f"{name}_{timestamp}.log"
    output_filename = os.path.join(output_dir, output_filename)

    match output_format:
        case "table":
            formatter = TableFormatter()
        case "csv":
            formatter = CSVFormatter()
        case "json":
            formatter = JSONFormatter()
        case _:
            logger.error(f"Invalid output format: {output_format}")
            sys.exit(1)

    formatted_results = formatter.format(results)

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(formatted_results)
        logger.info(f"Results written to {output_filename}")
    except Exception as e:
        logger.error(f"Failed to write results to file: {e}")
    return formatted_results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MongoDB Index Performance Tester")
    parser.add_argument("--connection", type=str, default=DEFAULT_CONFIG["connection"])
    parser.add_argument("--iterations", type=int, default=DEFAULT_CONFIG["iterations"])
    parser.add_argument(
        "--warmup", type=int, default=DEFAULT_CONFIG["warmup_iterations"]
    )
    parser.add_argument(
        "--sample-interval", type=int, default=DEFAULT_CONFIG["sample_interval"]
    )
    parser.add_argument(
        "--output-format",
        choices=["table", "csv", "json"],
        default=DEFAULT_CONFIG["output_format"],
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output directory",
    )
    parser.add_argument(
        "--test-config",
        type=str,
        help="Test case configuration file path",
        required=True,
    )
    args = parser.parse_args()

    test_queries = load_test_queries(args.test_config)
    tested_queries = set()

    for attempt in range(DEFAULT_CONFIG["max_retries"]):
        try:
            with MongoDBConnection(args.connection) as conn:
                tester = IndexPerformanceTester(conn)
                tester.output_format = args.output_format

                for query in test_queries:
                    if hash(query) in tested_queries:
                        continue
                    logger.info(f"Testing Query {query.query}")
                    results = []
                    tested_hints = set()
                    for hint in query.hints:
                        if tuple(hint.items()) in tested_hints:
                            continue
                        logger.info(f"Testing Query with hint {hint}")
                        result = tester.test_index_performance(
                            database=query.database,
                            collection=query.collection,
                            query=query.query,
                            index_hint=hint,
                            iterations=args.iterations,
                            warmup_iterations=args.warmup,
                            sample_interval=args.sample_interval,
                        )

                        if result.error is None:
                            results.append(result)
                            tested_hints.add(tuple(hint.items()))
                        else:
                            logger.error(
                                f"Error during performance test: {result.error}"
                            )

                    # Output and save results
                    formatted_results = save_results(
                        results, args.output_format, args.output_dir, query.name
                    )

                    print("\nPerformance Test Results:")
                    print(formatted_results)
                    tested_queries.add(hash(query))
            break

        except errors.ConnectionFailure as e:
            if attempt < DEFAULT_CONFIG["max_retries"] - 1:
                delay = DEFAULT_CONFIG["retry_delay_base"] ** attempt
                logger.warning(
                    f"Connection failed, retrying in {delay}s ({attempt+1}/{DEFAULT_CONFIG['max_retries']})..."
                )
                time.sleep(delay)
            else:
                logger.error("Exceeded maximum retries. Exiting.")
                sys.exit(1)

if __name__ == "__main__":
    main()
