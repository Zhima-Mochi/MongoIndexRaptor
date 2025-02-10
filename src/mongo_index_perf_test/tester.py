import time
import statistics
from typing import Dict, Any, List, Tuple
from pymongo import errors

from .config import DEFAULT_CONFIG, logger
from .connection import MongoDBConnection
from .models import TestResult

class IndexPerformanceTester:
    """Test MongoDB index performance"""

    def __init__(self, connection: MongoDBConnection):
        self.connection = connection
        self.output_format = DEFAULT_CONFIG["output_format"]

    def test_index_performance(
        self,
        database: str,
        collection: str,
        query: Dict[str, Any],
        index_hint: Dict[str, int],
        iterations: int = DEFAULT_CONFIG["iterations"],
        warmup_iterations: int = DEFAULT_CONFIG["warmup_iterations"],
        sample_interval: int = DEFAULT_CONFIG["sample_interval"],
    ) -> TestResult:
        """Test query performance with specific index"""
        try:
            self._clear_plan_cache(database, collection)

            # Warm-up phase
            self._perform_warmup(
                database, collection, query, index_hint, warmup_iterations
            )

            # Testing phase
            times, docs_examined, keys_examined, docs_returned = self._perform_testing(
                database, collection, query, index_hint, iterations, sample_interval
            )

            return self._calculate_results(
                query=query,
                index_hint=index_hint,
                iteration=iterations,
                warmup_iteration=warmup_iterations,
                sample_interval=sample_interval,
                times=times,
                docs_examined=docs_examined,
                keys_examined=keys_examined,
                docs_returned=docs_returned,
            )

        except errors.PyMongoError as e:
            logger.error(f"Error during performance test: {e}")
            return TestResult(
                query=query,
                hint=index_hint,
                iteration=iterations,
                warmup_iteration=warmup_iterations,
                sample_interval=sample_interval,
                avg_time=0,
                min_time=0,
                max_time=0,
                stdev_time=0,
                error=str(e),
            )

    def _clear_plan_cache(self, database: str, collection: str):
        """Clear query plan cache based on MongoDB version"""
        logger.info(f"Clearing plan cache for {database}.{collection}")
        build_info = self.connection.client.admin.command("buildInfo")
        version = build_info.get("version", "")

        def parse_version(version_str: str) -> tuple:
            return tuple(map(int, (version_str.split("."))))

        try:
            if parse_version(version) >= parse_version("4.4"):
                self.connection.client.admin.command(
                    {"planCacheClear": f"{database}.{collection}"}
                )
            else:
                self.connection.client.command(
                    "planCacheClear",
                    collection,
                    database=database,
                )
        except errors.PyMongoError as e:
            logger.warning(f"Failed to clear plan cache: {e}")

    def _perform_warmup(
        self,
        database: str,
        collection: str,
        query: Dict[str, Any],
        index_hint: Dict[str, int],
        warmup_iterations: int,
    ):
        """Perform warm-up iterations"""
        logger.info(f"Warming up ({warmup_iterations} iterations)")
        for i in range(warmup_iterations):
            if (i + 1) % max(1, warmup_iterations // 5) == 0:
                logger.debug(f"Warmup progress: {i+1}/{warmup_iterations}")
            coll = self.connection.client[database][collection]
            list(self._build_query_cursor(coll, query, index_hint).limit(0))

    def _perform_testing(
        self,
        database: str,
        collection: str,
        query: Dict[str, Any],
        index_hint: Dict[str, int],
        iterations: int,
        sample_interval: int,
    ) -> Tuple[List[float], List[int], List[int], List[int]]:
        """Perform testing iterations"""
        logger.info(f"Testing query")
        times = []
        docs_examined = []
        keys_examined = []
        docs_returned = []

        for i in range(iterations):
            start_time = time.perf_counter()
            coll = self.connection.client[database][collection]

            cursor = self._build_query_cursor(coll, query, index_hint)
            result_count = len(list(cursor))
            docs_returned.append(result_count)

            elapsed = time.perf_counter() - start_time
            times.append(elapsed)

            if sample_interval > 0 and (
                i % sample_interval == 0 or i == iterations - 1
            ):
                self._collect_execution_stats(
                    database,
                    collection,
                    query,
                    index_hint,
                    docs_examined,
                    keys_examined,
                )

        return times, docs_examined, keys_examined, docs_returned

    def _collect_execution_stats(
        self,
        database: str,
        collection: str,
        query: Dict[str, Any],
        index_hint: Dict[str, int],
        docs_examined: List[int],
        keys_examined: List[int],
    ):
        """Collect execution statistics"""
        coll = self.connection.client[database][collection]
        explain_result = self._build_query_cursor(coll, query, index_hint).explain()
        stats = explain_result.get("executionStats", {})
        docs_examined.append(stats.get("totalDocsExamined", 0))
        keys_examined.append(stats.get("totalKeysExamined", 0))

    def _calculate_results(
        self,
        query: Dict[str, Any],
        index_hint: Dict[str, int],
        iteration: int,
        warmup_iteration: int,
        sample_interval: int,
        times: List[float],
        docs_examined: List[int],
        keys_examined: List[int],
        docs_returned: List[int],
    ) -> TestResult:
        """Calculate statistical results"""
        logger.info(f"Calculating results")
        sorted_times = sorted(times)
        return TestResult(
            query=query,
            hint=index_hint,
            iteration=iteration,
            warmup_iteration=warmup_iteration,
            sample_interval=sample_interval,
            avg_time=statistics.mean(sorted_times),
            min_time=sorted_times[0],
            max_time=sorted_times[-1],
            stdev_time=statistics.stdev(sorted_times) if len(sorted_times) > 1 else 0.0,
            percentile_95=(
                statistics.quantiles(sorted_times, n=100)[94]
                if len(sorted_times) >= 5
                else 0.0
            ),
            percentile_99=(
                statistics.quantiles(sorted_times, n=100)[98]
                if len(sorted_times) >= 5
                else 0.0
            ),
            avg_docs_examined=statistics.mean(docs_examined) if docs_examined else 0.0,
            avg_keys_examined=statistics.mean(keys_examined) if keys_examined else 0.0,
            avg_docs_returned=statistics.mean(docs_returned) if docs_returned else 0.0,
        )
    
    def _build_query_cursor(self, coll, query, index_hint):
        command = coll.find(query['filter']) if query.get('project') is None else coll.find(query['filter'], query['project'])
        if query.get('sort'):
            command = command.sort(query['sort'])
        if query.get('skip'):
            command = command.skip(query['skip'])
        if query.get('limit'):
            command = command.limit(query['limit'])
        if index_hint:
            command = command.hint(index_hint)
        return command