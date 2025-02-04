import json
import os
from datetime import datetime
from typing import Dict, Optional

from .logger import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """Manages checkpoints and state for the orchestrator"""

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """
        Initialize the checkpoint manager

        Args:
            checkpoint_dir (str): Directory to store checkpoints
        """
        self.checkpoint_dir = checkpoint_dir
        self._ensure_checkpoint_dir()

    def _ensure_checkpoint_dir(self):
        """Ensure the checkpoint directory exists"""
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        logger.info(f"Checkpoint directory ensured at: {self.checkpoint_dir}")

    def create_checkpoint(self, job_id: str, state: Dict) -> str:
        """
        Create a checkpoint for the current state

        Args:
            job_id (str): Unique identifier for the job
            state (Dict): Current state to checkpoint

        Returns:
            str: Path to the created checkpoint file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = f"{job_id}_{timestamp}.json"
            checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_file)

            # Add metadata to the state
            checkpoint_data = {"job_id": job_id, "timestamp": timestamp, "state": state}

            # Write checkpoint to file
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"Created checkpoint: {checkpoint_path}")
            return checkpoint_path

        except Exception as e:
            logger.error(f"Error creating checkpoint: {str(e)}")
            raise

    def load_checkpoint(self, job_id: str, timestamp: Optional[str] = None) -> Dict:
        """
        Load a checkpoint for the given job

        Args:
            job_id (str): Job ID to load checkpoint for
            timestamp (Optional[str]): Specific timestamp to load, if None loads latest

        Returns:
            Dict: The checkpoint data
        """
        try:
            # List all checkpoints for this job
            checkpoints = [
                f
                for f in os.listdir(self.checkpoint_dir)
                if f.startswith(job_id) and f.endswith(".json")
            ]

            if not checkpoints:
                raise FileNotFoundError(f"No checkpoints found for job {job_id}")

            # If timestamp not specified, get latest checkpoint
            if timestamp is None:
                checkpoint_file = sorted(checkpoints)[-1]
            else:
                checkpoint_file = f"{job_id}_{timestamp}.json"
                if checkpoint_file not in checkpoints:
                    raise FileNotFoundError(f"Checkpoint not found: {checkpoint_file}")

            checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_file)

            # Load and return checkpoint data
            with open(checkpoint_path, "r") as f:
                checkpoint_data = json.load(f)

            logger.info(f"Loaded checkpoint: {checkpoint_path}")
            return checkpoint_data

        except Exception as e:
            logger.error(f"Error loading checkpoint: {str(e)}")
            raise

    def list_checkpoints(self, job_id: Optional[str] = None) -> list:
        """
        List available checkpoints

        Args:
            job_id (Optional[str]): If provided, only list checkpoints for this job

        Returns:
            list: List of checkpoint files
        """
        try:
            checkpoints = os.listdir(self.checkpoint_dir)

            if job_id:
                checkpoints = [
                    cp
                    for cp in checkpoints
                    if cp.startswith(job_id) and cp.endswith(".json")
                ]

            return sorted(checkpoints)

        except Exception as e:
            logger.error(f"Error listing checkpoints: {str(e)}")
            raise
