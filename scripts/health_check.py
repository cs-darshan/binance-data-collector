#!/usr/bin/env python3
"""
Health monitoring script for Binance Data Collector
Checks service status, data freshness, and system resources
"""

import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import csv
import argparse

class HealthMonitor:
    def __init__(self, data_dir='/opt/binance-data-collector/data'):
        self.data_dir = Path(data_dir)
        self.service_name = 'binance-collector'

    def check_service_status(self):
        """Check if systemd service is running"""
        try:
            result = subprocess.run(['systemctl', 'is-active', self.service_name], 
                                  capture_output=True, text=True)
            return result.stdout.strip() == 'active'
        except Exception as e:
            print(f"Error checking service status: {e}")
            return False

    def check_data_freshness(self, max_age_minutes=5):
        """Check if data files are being updated recently"""
        try:
            # Find the most recent CSV file
            csv_files = list(self.data_dir.glob('binance_data_*.csv'))
            if not csv_files:
                return False, "No data files found"

            latest_file = max(csv_files, key=os.path.getmtime)
            file_age = datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)

            if file_age > timedelta(minutes=max_age_minutes):
                return False, f"Latest file is {file_age} old"

            # Check if file has recent data
            try:
                with open(latest_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    lines = list(reader)

                if not lines:
                    return False, "No data in file"

                # Check timestamp of last entry
                last_timestamp = int(lines[-1][0])
                last_data_time = datetime.fromtimestamp(last_timestamp / 1000)
                data_age = datetime.now() - last_data_time

                if data_age > timedelta(minutes=max_age_minutes):
                    return False, f"Last data entry is {data_age} old"

                return True, f"Data is fresh (last entry: {data_age} ago)"

            except Exception as e:
                return False, f"Error reading data file: {e}"

        except Exception as e:
            return False, f"Error checking data freshness: {e}"

    def check_disk_space(self, min_free_gb=1):
        """Check available disk space"""
        try:
            result = subprocess.run(['df', '-BG', str(self.data_dir)], 
                                  capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                fields = lines[1].split()
                available_gb = int(fields[3].replace('G', ''))

                if available_gb < min_free_gb:
                    return False, f"Only {available_gb}GB free space remaining"

                return True, f"{available_gb}GB free space available"
        except Exception as e:
            return False, f"Error checking disk space: {e}"

    def check_log_errors(self, hours=1):
        """Check for recent errors in service logs"""
        try:
            since_time = f"{hours} hours ago"
            result = subprocess.run([
                'journalctl', '-u', self.service_name, 
                '--since', since_time, '--no-pager'
            ], capture_output=True, text=True)

            log_lines = result.stdout.split('\n')
            error_lines = [line for line in log_lines if 'ERROR' in line]
            warning_lines = [line for line in log_lines if 'WARNING' in line]

            if error_lines:
                return False, f"{len(error_lines)} errors found in last {hours}h"
            elif warning_lines:
                return True, f"{len(warning_lines)} warnings found in last {hours}h"
            else:
                return True, f"No errors in last {hours}h"

        except Exception as e:
            return False, f"Error checking logs: {e}"

    def get_data_stats(self):
        """Get statistics about collected data"""
        try:
            csv_files = list(self.data_dir.glob('binance_data_*.csv'))
            if not csv_files:
                return "No data files found"

            total_records = 0
            latest_file = None
            latest_time = 0

            for file in csv_files:
                try:
                    with open(file, 'r') as f:
                        reader = csv.reader(f)
                        next(reader)  # Skip header
                        lines = list(reader)
                        total_records += len(lines)

                        if lines:
                            file_latest = int(lines[-1][0])
                            if file_latest > latest_time:
                                latest_time = file_latest
                                latest_file = file
                except:
                    continue

            if latest_file:
                latest_datetime = datetime.fromtimestamp(latest_time / 1000)
                return f"Total records: {total_records}, Latest: {latest_datetime}"
            else:
                return "No valid data found"

        except Exception as e:
            return f"Error getting stats: {e}"

    def run_health_check(self):
        """Run complete health check"""
        print("🏥 Binance Data Collector Health Check")
        print("=" * 50)

        checks = [
            ("Service Status", self.check_service_status),
            ("Data Freshness", lambda: self.check_data_freshness(5)),
            ("Disk Space", lambda: self.check_disk_space(1)),
            ("Recent Errors", lambda: self.check_log_errors(1))
        ]

        all_healthy = True

        for check_name, check_func in checks:
            try:
                if check_name == "Service Status":
                    result = check_func()
                    status = "✅ HEALTHY" if result else "❌ UNHEALTHY"
                    message = "Running" if result else "Not running"
                else:
                    result, message = check_func()
                    status = "✅ HEALTHY" if result else "❌ UNHEALTHY"

                print(f"{check_name:<15}: {status} - {message}")

                if not result:
                    all_healthy = False

            except Exception as e:
                print(f"{check_name:<15}: ❌ ERROR - {e}")
                all_healthy = False

        print("\n📊 Data Statistics:")
        print(f"   {self.get_data_stats()}")

        print("\n" + "=" * 50)
        overall_status = "✅ SYSTEM HEALTHY" if all_healthy else "⚠️  ISSUES DETECTED"
        print(f"Overall Status: {overall_status}")

        return all_healthy

def main():
    parser = argparse.ArgumentParser(description='Monitor Binance Data Collector health')
    parser.add_argument('data_dir', nargs='?', default='/opt/binance-data-collector/data',
                       help='Data directory path')

    args = parser.parse_args()

    monitor = HealthMonitor(args.data_dir)
    healthy = monitor.run_health_check()
    sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
