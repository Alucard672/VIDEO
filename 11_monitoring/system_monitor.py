#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控模块
提供系统资源监控、性能监控和告警功能
"""

import psutil
import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import threading
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    process_count: int
    temperature: float = 0.0

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.db_path = Path("data/monitoring.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        self.is_monitoring = False
        self.monitor_thread = None
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "temperature": 70.0
        }
        
        # 存储历史网络数据用于计算速率
        self.last_network_stats = psutil.net_io_counters()
        self.last_check_time = time.time()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建系统指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                cpu_percent REAL NOT NULL,
                memory_percent REAL NOT NULL,
                disk_percent REAL NOT NULL,
                network_sent INTEGER NOT NULL,
                network_recv INTEGER NOT NULL,
                process_count INTEGER NOT NULL,
                temperature REAL DEFAULT 0.0,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建告警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                metric_value REAL NOT NULL,
                threshold_value REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建进程监控表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS process_monitor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name TEXT NOT NULL,
                pid INTEGER NOT NULL,
                cpu_percent REAL NOT NULL,
                memory_percent REAL NOT NULL,
                status TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("系统监控数据库初始化完成")
    
    def get_current_metrics(self) -> SystemMetrics:
        """获取当前系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 网络统计
            network_stats = psutil.net_io_counters()
            current_time = time.time()
            
            # 计算网络速率
            time_delta = current_time - self.last_check_time
            if time_delta > 0:
                network_sent = int((network_stats.bytes_sent - self.last_network_stats.bytes_sent) / time_delta)
                network_recv = int((network_stats.bytes_recv - self.last_network_stats.bytes_recv) / time_delta)
            else:
                network_sent = 0
                network_recv = 0
            
            self.last_network_stats = network_stats
            self.last_check_time = current_time
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 温度（如果可用）
            temperature = 0.0
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # 获取第一个温度传感器的值
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except:
                pass
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_sent=network_sent,
                network_recv=network_recv,
                process_count=process_count,
                temperature=temperature
            )
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_sent=0,
                network_recv=0,
                process_count=0
            )
    
    def save_metrics(self, metrics: SystemMetrics):
        """保存系统指标到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, disk_percent, 
                 network_sent, network_recv, process_count, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp,
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.disk_percent,
                metrics.network_sent,
                metrics.network_recv,
                metrics.process_count,
                metrics.temperature
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存系统指标失败: {e}")
    
    def check_alerts(self, metrics: SystemMetrics):
        """检查告警条件"""
        alerts = []
        
        # 检查CPU使用率
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alert = {
                "alert_type": "cpu_high",
                "message": f"CPU使用率过高: {metrics.cpu_percent:.1f}%",
                "severity": "warning" if metrics.cpu_percent < 90 else "critical",
                "metric_value": metrics.cpu_percent,
                "threshold_value": self.alert_thresholds["cpu_percent"],
                "timestamp": metrics.timestamp
            }
            alerts.append(alert)
        
        # 检查内存使用率
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alert = {
                "alert_type": "memory_high",
                "message": f"内存使用率过高: {metrics.memory_percent:.1f}%",
                "severity": "warning" if metrics.memory_percent < 95 else "critical",
                "metric_value": metrics.memory_percent,
                "threshold_value": self.alert_thresholds["memory_percent"],
                "timestamp": metrics.timestamp
            }
            alerts.append(alert)
        
        # 检查磁盘使用率
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alert = {
                "alert_type": "disk_high",
                "message": f"磁盘使用率过高: {metrics.disk_percent:.1f}%",
                "severity": "warning" if metrics.disk_percent < 95 else "critical",
                "metric_value": metrics.disk_percent,
                "threshold_value": self.alert_thresholds["disk_percent"],
                "timestamp": metrics.timestamp
            }
            alerts.append(alert)
        
        # 检查温度
        if metrics.temperature > self.alert_thresholds["temperature"]:
            alert = {
                "alert_type": "temperature_high",
                "message": f"系统温度过高: {metrics.temperature:.1f}°C",
                "severity": "warning" if metrics.temperature < 80 else "critical",
                "metric_value": metrics.temperature,
                "threshold_value": self.alert_thresholds["temperature"],
                "timestamp": metrics.timestamp
            }
            alerts.append(alert)
        
        # 保存告警
        for alert in alerts:
            self.save_alert(alert)
            logger.warning(f"系统告警: {alert['message']}")
        
        return alerts
    
    def save_alert(self, alert: Dict):
        """保存告警记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts 
                (alert_type, message, severity, metric_value, threshold_value, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                alert["alert_type"],
                alert["message"],
                alert["severity"],
                alert["metric_value"],
                alert["threshold_value"],
                alert["timestamp"]
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存告警记录失败: {e}")
    
    def get_process_info(self) -> List[Dict]:
        """获取进程信息"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 1.0 or proc_info['memory_percent'] > 1.0:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent'],
                            'status': proc_info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:20]  # 返回前20个进程
            
        except Exception as e:
            logger.error(f"获取进程信息失败: {e}")
            return []
    
    def get_historical_data(self, hours: int = 24) -> List[Dict]:
        """获取历史数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT timestamp, cpu_percent, memory_percent, disk_percent, 
                       network_sent, network_recv, process_count, temperature
                FROM system_metrics 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (start_time.isoformat(),))
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'timestamp': row[0],
                    'cpu_percent': row[1],
                    'memory_percent': row[2],
                    'disk_percent': row[3],
                    'network_sent': row[4],
                    'network_recv': row[5],
                    'process_count': row[6],
                    'temperature': row[7]
                })
            
            conn.close()
            return data
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return []
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """获取最近的告警"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT alert_type, message, severity, metric_value, 
                       threshold_value, timestamp, resolved
                FROM alerts 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (start_time.isoformat(),))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'alert_type': row[0],
                    'message': row[1],
                    'severity': row[2],
                    'metric_value': row[3],
                    'threshold_value': row[4],
                    'timestamp': row[5],
                    'resolved': bool(row[6])
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"获取告警记录失败: {e}")
            return []
    
    def start_monitoring(self, interval: int = 60):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("监控已在运行中")
            return
        
        self.is_monitoring = True
        
        def monitor_loop():
            logger.info(f"开始系统监控，间隔: {interval}秒")
            
            while self.is_monitoring:
                try:
                    # 获取系统指标
                    metrics = self.get_current_metrics()
                    
                    # 保存指标
                    self.save_metrics(metrics)
                    
                    # 检查告警
                    self.check_alerts(metrics)
                    
                    # 清理旧数据（保留7天）
                    self.cleanup_old_data(days=7)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"监控循环错误: {e}")
                    time.sleep(interval)
            
            logger.info("系统监控已停止")
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("系统监控已停止")
    
    def cleanup_old_data(self, days: int = 7):
        """清理旧数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # 清理旧的系统指标数据
            cursor.execute('''
                DELETE FROM system_metrics 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            # 清理旧的告警数据
            cursor.execute('''
                DELETE FROM alerts 
                WHERE timestamp < ? AND resolved = TRUE
            ''', (cutoff_time.isoformat(),))
            
            # 清理旧的进程监控数据
            cursor.execute('''
                DELETE FROM process_monitor 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"清理了{days}天前的旧数据")
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
    
    def get_system_summary(self) -> Dict:
        """获取系统摘要"""
        try:
            metrics = self.get_current_metrics()
            processes = self.get_process_info()
            recent_alerts = self.get_recent_alerts(hours=1)
            
            # 系统负载评估
            load_level = "正常"
            if metrics.cpu_percent > 80 or metrics.memory_percent > 85:
                load_level = "高负载"
            elif metrics.cpu_percent > 60 or metrics.memory_percent > 70:
                load_level = "中等负载"
            
            summary = {
                "current_metrics": {
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "disk_percent": metrics.disk_percent,
                    "network_sent": metrics.network_sent,
                    "network_recv": metrics.network_recv,
                    "process_count": metrics.process_count,
                    "temperature": metrics.temperature
                },
                "load_level": load_level,
                "top_processes": processes[:5],
                "recent_alerts_count": len(recent_alerts),
                "critical_alerts_count": len([a for a in recent_alerts if a['severity'] == 'critical']),
                "monitoring_status": "运行中" if self.is_monitoring else "已停止",
                "last_update": metrics.timestamp
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取系统摘要失败: {e}")
            return {}

def main():
    """主函数"""
    monitor = SystemMonitor()
    
    # 获取当前指标
    metrics = monitor.get_current_metrics()
    print(f"当前系统指标:")
    print(f"CPU: {metrics.cpu_percent:.1f}%")
    print(f"内存: {metrics.memory_percent:.1f}%")
    print(f"磁盘: {metrics.disk_percent:.1f}%")
    print(f"进程数: {metrics.process_count}")
    
    # 获取进程信息
    processes = monitor.get_process_info()
    print(f"\n前5个高CPU使用率进程:")
    for proc in processes[:5]:
        print(f"  {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}%")
    
    # 开始监控（测试模式，短时间间隔）
    print(f"\n开始监控测试...")
    monitor.start_monitoring(interval=10)
    
    try:
        time.sleep(30)  # 监控30秒
    except KeyboardInterrupt:
        pass
    
    monitor.stop_monitoring()
    print("监控测试完成")

if __name__ == "__main__":
    main()
