"""
日志管理模块
记录系统操作、性能指标和错误信息
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
try:
    from config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH
except ImportError:
    from backend.config import Config
    PROCESSED_DATA_PATH = Config.PROCESSED_DATA_PATH


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class OperationLogger:
    """操作日志记录器"""
    
    def __init__(self, log_file: str = "operation_log.jsonl", max_entries: int = 10000):
        self.log_dir = PROCESSED_DATA_PATH / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / log_file
        self.max_entries = max_entries
        self.entries = []
        
    def log(self, 
            operation: str,
            level: LogLevel = LogLevel.INFO,
            details: Dict[str, Any] = None,
            user_id: str = None,
            duration_ms: float = None):
        """
        记录操作日志
        
        Args:
            operation: 操作名称
            level: 日志级别
            details: 详细信息
            user_id: 用户ID
            duration_ms: 操作耗时(毫秒)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "level": level.value,
            "details": details or {},
            "user_id": user_id,
            "duration_ms": duration_ms
        }
        
        self.entries.append(entry)
        
        # 实时写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # 控制内存中的条目数
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
    
    def log_search(self, query: str, results_count: int, duration_ms: float, **kwargs):
        """记录检索操作"""
        self.log(
            operation="search",
            level=LogLevel.INFO,
            details={
                "query": query[:200],
                "results_count": results_count,
                **kwargs
            },
            duration_ms=duration_ms
        )
    
    def log_generation(self, 
                      query: str, 
                      model: str, 
                      duration_ms: float,
                      success: bool = True,
                      error: str = None,
                      tokens_used: int = None,
                      **kwargs):
        """记录生成操作"""
        self.log(
            operation="llm_generation",
            level=LogLevel.INFO if success else LogLevel.ERROR,
            details={
                "query": query[:200],
                "model": model,
                "success": success,
                "error": error,
                "tokens_used": tokens_used,
                **kwargs
            },
            duration_ms=duration_ms
        )
    
    def log_classification(self,
                          text: str,
                          question_type: str,
                          urgency: str,
                          duration_ms: float,
                          **kwargs):
        """记录分类操作"""
        self.log(
            operation="classification",
            level=LogLevel.INFO,
            details={
                "text": text[:200],
                "question_type": question_type,
                "urgency": urgency,
                **kwargs
            },
            duration_ms=duration_ms
        )
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取日志统计"""
        if not self.log_file.exists():
            return {
                "total_operations": 0,
                "operations_by_type": {},
                "avg_duration_by_type": {},
                "error_rate": 0.0
            }
        
        # 读取日志文件
        operations = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    operations.append(entry)
                except:
                    continue
        
        # 统计
        total = len(operations)
        by_type = {}
        durations = {}
        errors = 0
        
        for op in operations:
            op_type = op.get("operation", "unknown")
            by_type[op_type] = by_type.get(op_type, 0) + 1
            
            if op_type not in durations:
                durations[op_type] = []
            if op.get("duration_ms"):
                durations[op_type].append(op["duration_ms"])
            
            if op.get("level") == "error":
                errors += 1
        
        # 计算平均耗时
        avg_durations = {
            op_type: sum(times) / len(times) if times else 0
            for op_type, times in durations.items()
        }
        
        return {
            "total_operations": total,
            "operations_by_type": by_type,
            "avg_duration_by_type": avg_durations,
            "error_rate": errors / total if total > 0 else 0.0,
            "log_file": str(self.log_file)
        }
    
    def get_recent_logs(self, n: int = 10) -> list:
        """获取最近的日志"""
        if not self.log_file.exists():
            return []
        
        logs = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    logs.append(entry)
                except:
                    continue
        
        return logs[-n:]


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            "api_calls": 0,
            "api_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens": 0,
            "start_time": time.time()
        }
    
    def record_api_call(self, success: bool = True, tokens: int = 0):
        """记录API调用"""
        self.metrics["api_calls"] += 1
        if not success:
            self.metrics["api_errors"] += 1
        self.metrics["total_tokens"] += tokens
    
    def record_cache(self, hit: bool):
        """记录缓存访问"""
        if hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        uptime = time.time() - self.metrics["start_time"]
        total_cache = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        
        return {
            "uptime_seconds": int(uptime),
            "api_calls": self.metrics["api_calls"],
            "api_errors": self.metrics["api_errors"],
            "api_success_rate": 1 - (self.metrics["api_errors"] / self.metrics["api_calls"]) 
                               if self.metrics["api_calls"] > 0 else 1.0,
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "cache_hit_rate": self.metrics["cache_hits"] / total_cache 
                            if total_cache > 0 else 0.0,
            "total_tokens": self.metrics["total_tokens"],
            "avg_tokens_per_call": self.metrics["total_tokens"] / self.metrics["api_calls"]
                                  if self.metrics["api_calls"] > 0 else 0
        }


# 全局实例
_logger_instance: Optional[OperationLogger] = None
_monitor_instance: Optional[PerformanceMonitor] = None


def get_logger() -> OperationLogger:
    """获取全局日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = OperationLogger()
    return _logger_instance


def get_monitor() -> PerformanceMonitor:
    """获取全局监控实例"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance


if __name__ == "__main__":
    # 测试
    print("="*80)
    print("📝 日志系统测试")
    print("="*80)
    
    logger = OperationLogger()
    monitor = PerformanceMonitor()
    
    # 模拟操作
    print("\n模拟操作...")
    
    # 检索操作
    logger.log_search(
        query="エンジェルガチョを購入したのですがダイヤがもらえない",
        results_count=3,
        duration_ms=45.2
    )
    print("✓ 记录检索操作")
    
    # 生成操作
    logger.log_generation(
        query="イベントのアイテムが反映されない",
        model="qwen3.5-plus",
        duration_ms=1250.5,
        success=True,
        tokens_used=850
    )
    print("✓ 记录生成操作")
    monitor.record_api_call(success=True, tokens=850)
    
    # 分类操作
    logger.log_classification(
        text="至急対応してください！",
        question_type="充值问题",
        urgency="high",
        duration_ms=12.3
    )
    print("✓ 记录分类操作")
    
    # 缓存记录
    monitor.record_cache(hit=True)
    monitor.record_cache(hit=False)
    print("✓ 记录缓存访问")
    
    # 统计信息
    print("\n" + "="*80)
    print("📊 日志统计")
    print("="*80)
    stats = logger.get_stats()
    print(f"总操作数: {stats['total_operations']}")
    print(f"操作类型分布: {stats['operations_by_type']}")
    print(f"平均耗时: {stats['avg_duration_by_type']}")
    
    print("\n" + "="*80)
    print("📈 性能监控")
    print("="*80)
    metrics = monitor.get_metrics()
    print(f"API调用: {metrics['api_calls']}")
    print(f"API成功率: {metrics['api_success_rate']:.1%}")
    print(f"缓存命中率: {metrics['cache_hit_rate']:.1%}")
    print(f"总Token数: {metrics['total_tokens']}")
