# -*- coding: utf-8 -*-
"""
Batch Submitter - Submit batch input to OpenAI Batch API
批处理提交器 - 将批处理输入提交到OpenAI批处理API

Reads OpenAI config.json and submits data/3.batch_input files to OpenAI Batch API.
读取OpenAI config.json并将data/3.batch_input文件提交到OpenAI批处理API。
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("Warning: openai package not found. Install with: pip install openai")
    OpenAI = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchSubmitter:
    """
    Submit batch input files to OpenAI Batch API
    将批处理输入文件提交到OpenAI批处理API
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize BatchSubmitter

        Args:
            config_path: Path to OpenAI configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.client = None

        if OpenAI:
            self.client = OpenAI(api_key=self.config.get("api_key"))
        else:
            logger.warning("OpenAI client not available - install openai package")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load OpenAI configuration / 加载OpenAI配置"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            try:
                full_config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse config.json: {e}")

        # Handle nested config structure (check 'openai' or top-level)
        config = full_config.get("openai", full_config)

        if not isinstance(config, dict):
            raise ValueError(f"Config must be a dictionary, got {type(config)}")

        if "api_key" not in config:
            raise ValueError(f"Missing 'api_key' in config (either at top-level or under 'openai' key). Found keys: {list(config.keys())}")

        return config

    def submit_batch_files(self, batch_input_dir: str = "data/3.batch_input",
                          output_dir: str = "data/4.batch_output") -> Dict[str, Any]:
        """
        Submit all batch input files to OpenAI Batch API
        将所有批处理输入文件提交到OpenAI批处理API

        Args:
            batch_input_dir: Directory containing batch input JSONL files
            output_dir: Directory to save batch job information

        Returns:
            Dictionary with submission results
        """
        input_dir = Path(batch_input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not input_dir.exists():
            raise FileNotFoundError(f"Batch input directory not found: {input_dir}")

        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        results = {
            "submitted_jobs": [],
            "failed_submissions": [],
            "timestamp": datetime.now().isoformat()
        }

        # Find all batch input files
        batch_files = list(input_dir.glob("*_batch_input_*.jsonl"))
        logger.info(f"Found {len(batch_files)} batch input files")

        for batch_file in batch_files:
            try:
                logger.info(f"Submitting batch file: {batch_file}")
                job_info = self._submit_single_batch(batch_file, output_dir)
                results["submitted_jobs"].append(job_info)

            except Exception as e:
                error_info = {
                    "file": str(batch_file),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results["failed_submissions"].append(error_info)
                logger.error(f"Failed to submit {batch_file}: {e}")

        # Save results
        results_file = output_dir / f"batch_submission_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Batch submission complete. Results saved to: {results_file}")
        return results

    def _submit_single_batch(self, batch_file: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Submit a single batch file to OpenAI
        将单个批处理文件提交到OpenAI
        """
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        # Upload the batch input file
        with open(batch_file, 'rb') as f:
            file_response = self.client.files.create(
                file=f,
                purpose="batch"
            )

        file_id = file_response.id
        logger.info(f"Uploaded batch file {batch_file.name}, file_id: {file_id}")

        # Create batch job
        batch_response = self.client.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )

        job_info = {
            "batch_file": str(batch_file),
            "file_id": file_id,
            "batch_id": batch_response.id,
            "status": batch_response.status,
            "created_at": datetime.now().isoformat(),
            "completion_window": batch_response.completion_window
        }

        # Save job info to output directory
        job_file = output_dir / f"batch_job_{batch_response.id}.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_info, f, indent=2, ensure_ascii=False)

        logger.info(f"Created batch job {batch_response.id}, status: {batch_response.status}")
        return job_info

    def check_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Check the status of a batch job
        检查批处理作业的状态

        Args:
            batch_id: Batch job ID

        Returns:
            Batch job status information
        """
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        batch = self.client.batches.retrieve(batch_id)

        status_info = {
            "batch_id": batch.id,
            "status": batch.status,
            "created_at": batch.created_at,
            "completed_at": getattr(batch, 'completed_at', None),
            "request_counts": getattr(batch, 'request_counts', None),
            "output_file_id": getattr(batch, 'output_file_id', None),
            "error_file_id": getattr(batch, 'error_file_id', None)
        }

        return status_info

    def download_batch_results(self, batch_id: str, output_dir: str = "data/4.batch_output") -> str:
        """
        Download batch results for a completed job
        下载已完成作业的批处理结果

        Args:
            batch_id: Batch job ID
            output_dir: Output directory for results

        Returns:
            Path to downloaded results file
        """
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get batch status
        batch = self.client.batches.retrieve(batch_id)

        if batch.status != "completed":
            raise ValueError(f"Batch job {batch_id} is not completed. Status: {batch.status}")

        # Download output file
        if batch.output_file_id:
            output_content = self.client.files.content(batch.output_file_id)
            output_file = output_dir / f"batch_results_{batch_id}.jsonl"

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_content.text)

            logger.info(f"Downloaded batch results to: {output_file}")
            return str(output_file)
        else:
            raise ValueError(f"No output file available for batch {batch_id}")

    def list_active_batches(self) -> List[Dict[str, Any]]:
        """
        List all active batch jobs
        列出所有活跃的批处理作业

        Returns:
            List of batch job information
        """
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        batches = self.client.batches.list()
        active_batches = []

        for batch in batches.data:
            if batch.status in ["validating", "in_progress", "finalizing"]:
                batch_info = {
                    "batch_id": batch.id,
                    "status": batch.status,
                    "created_at": batch.created_at,
                    "completion_window": batch.completion_window
                }
                active_batches.append(batch_info)

        return active_batches


def main():
    """Command line interface / 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Submit batch input to OpenAI Batch API")
    parser.add_argument("--config", "-c", default="config.json",
                       help="Path to OpenAI config.json file")
    parser.add_argument("--input-dir", "-i", default="data/3.batch_input",
                       help="Directory containing batch input files")
    parser.add_argument("--output-dir", "-o", default="data/4.batch_output",
                       help="Output directory for batch job information")
    parser.add_argument("--check-status", "-s", help="Check status of specific batch ID")
    parser.add_argument("--download-results", "-d", help="Download results for specific batch ID")
    parser.add_argument("--list-active", "-l", action="store_true",
                       help="List all active batch jobs")

    args = parser.parse_args()

    try:
        submitter = BatchSubmitter(config_path=args.config)

        if args.check_status:
            # Check specific batch status
            status = submitter.check_batch_status(args.check_status)
            print(f"Batch {args.check_status} status:")
            print(json.dumps(status, indent=2, ensure_ascii=False))

        elif args.download_results:
            # Download batch results
            result_file = submitter.download_batch_results(args.download_results, args.output_dir)
            print(f"Downloaded results to: {result_file}")

        elif args.list_active:
            # List active batches
            active = submitter.list_active_batches()
            print(f"Active batch jobs: {len(active)}")
            for batch in active:
                print(f"  {batch['batch_id']}: {batch['status']}")

        else:
            # Submit batch files
            results = submitter.submit_batch_files(
                batch_input_dir=args.input_dir,
                output_dir=args.output_dir
            )

            print("Batch submission complete!")
            print(f"Submitted jobs: {len(results['submitted_jobs'])}")
            print(f"Failed submissions: {len(results['failed_submissions'])}")

            if results['failed_submissions']:
                print("\nFailed submissions:")
                for failure in results['failed_submissions']:
                    print(f"  {failure['file']}: {failure['error']}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

# D:\Code\Python\python.exe  src/pipeline/batch_submitter.py --config config.json --input-dir ./data/3.batch_input/repo_fastapi_light/ --output-dir ./data/4.batch_output/repo_fastapi_light/