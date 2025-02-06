import json
from abc import ABC, abstractmethod
from typing import Sequence
from prettytable import PrettyTable
from .models import TestResult

class FormatterStrategy(ABC):
    @abstractmethod
    def format(self, results: Sequence[TestResult]) -> str:
        pass


class TableFormatter(FormatterStrategy):
    def format(self, results: Sequence[TestResult]) -> str:
        table = PrettyTable()
        table.title = "query: " + str(results[0].query)
        table.field_names = [
            "Index Hint",
            "Iteration",
            "Warmup Iteration",
            "Sample Interval",
            "Avg Time (s)",
            "Min Time (s)",
            "Max Time (s)",
            "StdDev",
            "95th %",
            "99th %",
            "Avg Docs",
            "Avg Keys",
            "Avg Returned",
        ]
        for result in results:
            table.add_row(
                [
                    str(result.hint),
                    f"{result.iteration}",
                    f"{result.warmup_iteration}",
                    f"{result.sample_interval}",
                    f"{result.avg_time:.6f}",
                    f"{result.min_time:.6f}",
                    f"{result.max_time:.6f}",
                    f"{result.stdev_time:.6f}",
                    f"{result.percentile_95:.6f}",
                    f"{result.percentile_99:.6f}",
                    f"{result.avg_docs_examined:.1f}",
                    f"{result.avg_keys_examined:.1f}",
                    f"{result.avg_docs_returned:.1f}",
                ]
            )
        return table.get_string()


class CSVFormatter(FormatterStrategy):
    def format(self, results: Sequence[TestResult]) -> str:
        header = "Query ID,Index Hint,Iteration,Warmup Iteration,Sample Interval,Avg Time (s),Min Time (s),Max Time (s),StdDev,95th %,99th %,Avg Docs,Avg Keys,Avg Returned,Error\n"
        lines = [header]
        for result in results:
            line = (
                f'"{result.query}",{result.hint},'
                f"{result.iteration},{result.warmup_iteration},{result.sample_interval},"
                f"{result.avg_time:.6f},{result.min_time:.6f},{result.max_time:.6f},"
                f"{result.stdev_time:.6f},{result.percentile_95:.6f},{result.percentile_99:.6f},"
                f"{result.avg_docs_examined:.1f},{result.avg_keys_examined:.1f},{result.avg_docs_returned:.1f},"
                f"{result.error or ''}\n"
            )
            lines.append(line)
        return "".join(lines)


class JSONFormatter(FormatterStrategy):
    def format(self, results: Sequence[TestResult]) -> str:
        return json.dumps([result.to_dict() for result in results], indent=2)
