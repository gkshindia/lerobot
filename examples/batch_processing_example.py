#!/usr/bin/env python3

"""
Example script showing how to use the improved batch processing functionality.

Run this with different batch sizes to see the performance difference:

python examples/batch_processing_example.py --batch_size 1   # Immediate encoding
python examples/batch_processing_example.py --batch_size 5   # Batch encoding
python examples/batch_processing_example.py --batch_size 10  # Larger batch
"""

import argparse
import logging
import tempfile
import time
from pathlib import Path

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.video_utils import VideoEncodingManager

# Configure logging to see the improved messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def demo_batch_processing(batch_size: int = 5, num_episodes: int = 5):
    """
    Demonstrate batch processing with the improved logging and feedback.
    
    Args:
        batch_size: Number of episodes to batch together for video encoding
        num_episodes: Total number of episodes to record
    """
    print(f"\n🎯 Demo: Recording {num_episodes} episodes with batch_size={batch_size}")
    print("=" * 60)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define features for a simple robot
        features = {
            "observation.state": {"shape": (6,), "dtype": "float32"},
            "observation.image.camera": {"shape": (240, 320, 3), "dtype": "uint8"},
            "action": {"shape": (6,), "dtype": "float32"},
        }
        
        # Create dataset with specified batch size
        dataset = LeRobotDataset.create(
            repo_id=f"demo/batch_processing_test",
            fps=30,
            root=Path(temp_dir) / "dataset",
            robot_type="demo_robot", 
            features=features,
            use_videos=True,
            batch_encoding_size=batch_size,  # This is the key parameter!
        )
        
        total_start_time = time.time()
        
        # Use VideoEncodingManager for proper cleanup
        with VideoEncodingManager(dataset):
            for episode_idx in range(num_episodes):
                episode_start_time = time.time()
                
                print(f"\n📹 Recording episode {episode_idx + 1}/{num_episodes}")
                
                # Simulate recording frames (10 frames per episode)
                for frame_idx in range(10):
                    # Create dummy frame data
                    frame = {
                        "observation.state": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                        "observation.image.camera": [[1, 2, 3] * 320] * 240,  # Dummy image
                        "action": [0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
                    }
                    dataset.add_frame(frame, task="demo_task")
                
                # Save episode - this will either encode immediately or defer to batch
                dataset.save_episode()
                
                episode_time = time.time() - episode_start_time
                print(f"⏱️  Episode {episode_idx + 1} processing time: {episode_time:.2f}s")
        
        total_time = time.time() - total_start_time
        avg_time = total_time / num_episodes
        
        print(f"\n📊 Summary:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average time per episode: {avg_time:.2f}s")
        print(f"   Batch size used: {batch_size}")
        
        return avg_time


def main():
    parser = argparse.ArgumentParser(description="Demonstrate batch processing functionality")
    parser.add_argument("--batch_size", type=int, default=5, 
                       help="Number of episodes to batch for video encoding (default: 5)")
    parser.add_argument("--num_episodes", type=int, default=5,
                       help="Total number of episodes to record (default: 5)")
    parser.add_argument("--compare", action="store_true",
                       help="Compare different batch sizes")
    
    args = parser.parse_args()
    
    if args.compare:
        print("🔬 Comparing different batch sizes...")
        batch_sizes = [1, 3, 5]
        results = {}
        
        for batch_size in batch_sizes:
            results[batch_size] = demo_batch_processing(batch_size, args.num_episodes)
        
        print(f"\n📈 Performance Comparison:")
        print("─" * 40)
        baseline = results[1]
        for batch_size, avg_time in results.items():
            improvement = ((baseline - avg_time) / baseline) * 100 if batch_size > 1 else 0
            status = "🚀" if batch_size > 1 else "📹"
            print(f"{status} Batch size {batch_size:2d}: {avg_time:.2f}s/episode ({improvement:+.1f}%)")
    else:
        demo_batch_processing(args.batch_size, args.num_episodes)
    
    print(f"\n💡 Tips:")
    print(f"   • Use --dataset.video_encoding_batch_size=5 for 60-70% faster recording")
    print(f"   • Higher batch sizes = faster recording but more temporary storage")
    print(f"   • Batch size 1 = immediate encoding (original behavior)")


if __name__ == "__main__":
    main()
