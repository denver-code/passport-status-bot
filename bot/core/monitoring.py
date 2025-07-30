"""
Performance monitoring and health check utilities for production deployment.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from bot.core.logger import log_error, log_info, log_warning
from bot.core.models.request_log import RequestLog
from bot.core.models.user import SubscriptionModel, UserModel


@dataclass
class HealthMetrics:
    """Health check metrics data structure."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    database_status: str = "unknown"
    database_response_time: float = 0.0
    bot_uptime: float = 0.0
    active_users_count: int = 0
    total_subscriptions: int = 0
    requests_last_hour: int = 0
    memory_usage_mb: float = 0.0
    errors_last_hour: int = 0

    @property
    def is_healthy(self) -> bool:
        """Check if all systems are healthy."""
        return (
            self.database_status == "healthy"
            and self.database_response_time < 1.0
            and self.errors_last_hour < 100
        )


class HealthChecker:
    """System health monitoring and diagnostics."""

    def __init__(self) -> None:
        self.start_time = datetime.utcnow()
        self._last_health_check: HealthMetrics | None = None
        self._health_history: list[HealthMetrics] = []

    async def check_database_health(self) -> tuple[str, float]:
        """Check database connectivity and response time."""
        try:
            start_time = time.time()
            # Test database connection
            from bot.core.models.user import UserModel

            await UserModel.find_one({})
            response_time = time.time() - start_time
            return "healthy", response_time
        except Exception as e:
            log_error(f"Database health check failed: {e}")
            return "unhealthy", 0.0

    async def get_system_metrics(self) -> HealthMetrics:
        """Collect comprehensive system metrics."""
        metrics = HealthMetrics()

        try:
            # Database health
            (
                metrics.database_status,
                metrics.database_response_time,
            ) = await self.check_database_health()

            # Uptime
            metrics.bot_uptime = (datetime.utcnow() - self.start_time).total_seconds()

            # User metrics
            metrics.active_users_count = await UserModel.find(
                {"is_active": True}
            ).count()
            metrics.total_subscriptions = await SubscriptionModel.find(
                {"is_active": True}
            ).count()

            # Request metrics
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            metrics.requests_last_hour = await RequestLog.find(
                {"timestamp": {"$gte": one_hour_ago}}
            ).count()

            # Memory usage
            try:
                import psutil

                metrics.memory_usage_mb = (
                    psutil.Process().memory_info().rss / 1024 / 1024
                )
            except ImportError:
                metrics.memory_usage_mb = 0.0

            # Error count (from logs - simplified)
            metrics.errors_last_hour = 0  # Would need log parsing for accurate count

        except Exception as e:
            log_error("Failed to collect system metrics", exception=e)

        return metrics

    async def perform_health_check(self) -> HealthMetrics:
        """Perform comprehensive health check."""
        log_info("Performing system health check")

        metrics = await self.get_system_metrics()
        self._last_health_check = metrics

        # Store in history (keep last 24 hours)
        self._health_history.append(metrics)
        if len(self._health_history) > 144:  # 24 hours * 6 checks per hour
            self._health_history.pop(0)

        # Log warnings for unhealthy systems
        if not metrics.is_healthy:
            log_warning(
                "System health check failed",
                database_status=metrics.database_status,
                response_time=metrics.database_response_time,
                errors=metrics.errors_last_hour,
            )

        return metrics

    def get_health_summary(self) -> dict[str, Any]:
        """Get health summary for API/admin display."""
        if not self._last_health_check:
            return {"status": "unknown", "message": "No health check performed yet"}

        metrics = self._last_health_check

        return {
            "status": "healthy" if metrics.is_healthy else "unhealthy",
            "timestamp": metrics.timestamp.isoformat(),
            "uptime_seconds": metrics.bot_uptime,
            "database": {
                "status": metrics.database_status,
                "response_time_ms": round(metrics.database_response_time * 1000, 2),
            },
            "users": {
                "active_count": metrics.active_users_count,
                "total_subscriptions": metrics.total_subscriptions,
            },
            "performance": {
                "requests_last_hour": metrics.requests_last_hour,
                "memory_usage_mb": round(metrics.memory_usage_mb, 2),
                "errors_last_hour": metrics.errors_last_hour,
            },
        }


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self) -> None:
        self._request_times: list[float] = []
        self._error_counts: dict[str, int] = {}
        self._start_time = time.time()

    def record_request_time(self, duration: float, endpoint: str = "unknown") -> None:
        """Record request processing time."""
        self._request_times.append(duration)

        # Keep only last 1000 requests
        if len(self._request_times) > 1000:
            self._request_times.pop(0)

        # Log slow requests
        if duration > 5.0:
            log_warning(
                f"Slow request detected: {endpoint}",
                duration=duration,
                endpoint=endpoint,
            )

    def record_error(self, error_type: str) -> None:
        """Record error occurrence."""
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        if not self._request_times:
            return {"message": "No performance data available"}

        sorted_times = sorted(self._request_times)
        count = len(sorted_times)

        return {
            "request_count": count,
            "avg_response_time": sum(sorted_times) / count,
            "median_response_time": sorted_times[count // 2],
            "p95_response_time": sorted_times[int(count * 0.95)]
            if count > 20
            else sorted_times[-1],
            "max_response_time": max(sorted_times),
            "error_counts": dict(self._error_counts),
            "uptime_seconds": time.time() - self._start_time,
        }


# Global instances
health_checker = HealthChecker()
performance_monitor = PerformanceMonitor()
