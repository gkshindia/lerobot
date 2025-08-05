#!/usr/bin/env python3

"""
Simple script to create individual Hugging Face model repositories from checkpoints
Based on LBST/t08_pick_and_place_policy_smolvla_files

Usage: python simple_checkpoint_creator.py
"""

import os
import shutil
import logging
from pathlib import Path

try:
    from huggingface_hub import HfApi, create_repo, hf_hub_download, upload_folder
except ImportError:
    print("Please install huggingface_hub: pip install huggingface_hub")
    exit(1)

# Configuration
SOURCE_REPO = "LBST/t08_pick_and_place_policy_smolvla_files"
TARGET_USER = "LBST"
BASE_REPO_NAME = "t08_pick_and_place_policy"

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_readme(checkpoint: str) -> str:
    """Create README content for the checkpoint repository."""
    return f"""---
library_name: lerobot
tags:
- robotics
- pick-and-place
- smolvla
- checkpoint-{checkpoint}
---

# T08 Pick and Place Policy - Checkpoint {checkpoint}

This model is a checkpoint from the training of a pick-and-place policy using SmolVLA architecture.

## Model Details

- **Checkpoint**: {checkpoint}
- **Architecture**: SmolVLA
- **Task**: Pick and Place (T08)
- **Training Step**: {checkpoint}

## Usage

You can evaluate this model using LeRobot:

```bash
python -m lerobot.scripts.eval \\
    --policy.path={TARGET_USER}/{BASE_REPO_NAME}_{checkpoint} \\
    --env.type=<your_environment> \\
    --eval.n_episodes=10 \\
    --policy.device=cuda
```

## Files

- `config.json`: Policy configuration
- `model.safetensors`: Model weights in SafeTensors format
- `train_config.json`: Complete training configuration for reproducibility

## Parent Repository

This checkpoint was extracted from: [{SOURCE_REPO}](https://huggingface.co/{SOURCE_REPO})

---

*Generated automatically from checkpoint {checkpoint}*
"""

def process_single_checkpoint(checkpoint: str, work_dir: Path):
    """Process a single checkpoint by downloading files and creating repository."""
    logger.info(f"Processing checkpoint {checkpoint}...")
    
    # Create working directory for this checkpoint
    checkpoint_dir = work_dir / checkpoint
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download files one by one to the checkpoint directory
        files_to_download = [
            f"{checkpoint}/pretrained_model/config.json",
            f"{checkpoint}/pretrained_model/model.safetensors",
            f"{checkpoint}/pretrained_model/train_config.json"
        ]
        
        for file_path in files_to_download:
            filename = Path(file_path).name
            logger.info(f"Downloading {file_path}...")
            
            # Download to a temporary location first
            downloaded_file = hf_hub_download(
                repo_id=SOURCE_REPO,
                filename=file_path,
                cache_dir=str(work_dir / "cache")
            )
            
            # Copy to our checkpoint directory
            target_path = checkpoint_dir / filename
            shutil.copy2(downloaded_file, target_path)
            logger.info(f"Copied {filename} to checkpoint directory")
        
        # Create README and .gitattributes
        logger.info("Creating README.md and .gitattributes...")
        (checkpoint_dir / "README.md").write_text(create_readme(checkpoint))
        (checkpoint_dir / ".gitattributes").write_text("""*.safetensors filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
""")
        
        # Create repository and upload
        repo_name = f"{BASE_REPO_NAME}_{checkpoint}"
        full_repo_name = f"{TARGET_USER}/{repo_name}"
        
        logger.info(f"Creating repository {full_repo_name}...")
        try:
            create_repo(repo_id=repo_name, repo_type="model", private=False, exist_ok=True)
        except Exception as e:
            logger.warning(f"Repository creation warning: {e}")
        
        logger.info(f"Uploading files to {full_repo_name}...")
        upload_folder(
            repo_id=full_repo_name,
            folder_path=checkpoint_dir,
            repo_type="model",
            commit_message=f"Add checkpoint {checkpoint} from {SOURCE_REPO}"
        )
        
        logger.info(f"✅ Successfully created {full_repo_name}")
        logger.info(f"Repository URL: https://huggingface.co/{full_repo_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to process checkpoint {checkpoint}: {e}")
        return False
    
    finally:
        # Clean up checkpoint directory
        if checkpoint_dir.exists():
            shutil.rmtree(checkpoint_dir)

def main():
    """Main function."""
    # Check authentication
    try:
        api = HfApi()
        user_info = api.whoami()
        logger.info(f"Authenticated as: {user_info['name']}")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        logger.error("Please run 'huggingface-cli login'")
        return 1
    
    # Create work directory
    work_dir = Path("./temp_work")
    work_dir.mkdir(exist_ok=True)
    
    try:
        # Define checkpoints to process - all 20 checkpoints
        checkpoints = [f"{i:06d}" for i in range(1000, 21000, 1000)]
        logger.info(f"Will process {len(checkpoints)} checkpoints: {checkpoints}")
        
        # Process each checkpoint
        successful = []
        failed = []
        
        for i, checkpoint in enumerate(checkpoints, 1):
            logger.info(f"Processing checkpoint {checkpoint} ({i}/{len(checkpoints)})...")
            
            if process_single_checkpoint(checkpoint, work_dir):
                successful.append(checkpoint)
            else:
                failed.append(checkpoint)
        
        # Summary
        logger.info("=" * 50)
        logger.info("PROCESSING COMPLETE")
        logger.info(f"Successful: {len(successful)} - {successful}")
        logger.info(f"Failed: {len(failed)} - {failed}")
        
        if failed:
            return 1
        
        logger.info("🎉 All checkpoints processed successfully!")
        return 0
        
    finally:
        # Cleanup work directory
        if work_dir.exists():
            shutil.rmtree(work_dir)

if __name__ == "__main__":
    exit(main())
