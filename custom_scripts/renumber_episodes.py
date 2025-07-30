#!/usr/bin/env python3

"""
Script to renumber episodes in a LeRobot dataset.

This script allows you to renumber episodes in the metadata files,
which is useful when you want to continue recording from a specific episode number
or reorganize your dataset numbering.

Usage:
    python custom_scripts/renumber_episodes.py --repo_id LBST/t06_pick_and_place --start_episode 0
    python custom_scripts/renumber_episodes.py --repo_id LBST/t06_pick_and_place --start_episode 66
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def renumber_episodes(repo_id: str, start_episode: int = 0, dry_run: bool = False):
    """
    Renumber episodes starting from start_episode.
    
    Args:
        repo_id: HuggingFace dataset repo ID (e.g., "LBST/t06_pick_and_place")
        start_episode: Starting episode number (default: 0)
        dry_run: If True, only show what would be changed without modifying files
    """
    
    # Dataset paths
    cache_dir = Path.home() / ".cache" / "huggingface" / "lerobot" / repo_id
    episodes_file = cache_dir / "meta" / "episodes.jsonl"
    info_file = cache_dir / "meta" / "info.json"
    
    # Check if files exist
    if not episodes_file.exists():
        print(f"❌ Error: episodes.jsonl not found at {episodes_file}")
        print(f"   Make sure the dataset {repo_id} exists in your cache.")
        return False
    
    if not info_file.exists():
        print(f"❌ Error: info.json not found at {info_file}")
        return False
    
    print(f"📂 Dataset cache location: {cache_dir}")
    print(f"📝 Episodes file: {episodes_file}")
    print(f"ℹ️  Info file: {info_file}")
    
    # Load current episodes
    episodes = []
    try:
        with open(episodes_file, 'r') as f:
            episodes = [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Error reading episodes file: {e}")
        return False
    
    if not episodes:
        print("❌ No episodes found in the dataset.")
        return False
    
    print(f"\n📊 Found {len(episodes)} episodes")
    print(f"🔢 Current episode range: {episodes[0]['episode_index']} to {episodes[-1]['episode_index']}")
    print(f"🎯 Target episode range: {start_episode} to {start_episode + len(episodes) - 1}")
    
    if dry_run:
        print("\n🔍 DRY RUN - Showing what would be changed:")
        for i, episode in enumerate(episodes):
            old_index = episode['episode_index']
            new_index = start_episode + i
            if old_index != new_index:
                print(f"   Episode {old_index} → {new_index}")
        print("\n💡 Run without --dry-run to apply changes.")
        return True
    
    # Create backups
    backup_episodes = episodes_file.with_suffix('.jsonl.bak')
    backup_info = info_file.with_suffix('.json.bak')
    
    try:
        shutil.copy2(episodes_file, backup_episodes)
        shutil.copy2(info_file, backup_info)
        print(f"\n💾 Created backups:")
        print(f"   {backup_episodes}")
        print(f"   {backup_info}")
    except Exception as e:
        print(f"❌ Error creating backups: {e}")
        return False
    
    # Renumber episodes
    changes_made = False
    for i, episode in enumerate(episodes):
        old_index = episode['episode_index']
        new_index = start_episode + i
        if old_index != new_index:
            episode['episode_index'] = new_index
            changes_made = True
            print(f"🔄 Renumbering episode {old_index} → {new_index}")
    
    if not changes_made:
        print("✅ No changes needed - episodes already numbered correctly.")
        return True
    
    # Write updated episodes
    try:
        with open(episodes_file, 'w') as f:
            for episode in episodes:
                f.write(json.dumps(episode) + '\n')
        print(f"✅ Updated {episodes_file}")
    except Exception as e:
        print(f"❌ Error writing episodes file: {e}")
        # Restore backup
        shutil.copy2(backup_episodes, episodes_file)
        return False
    
    # Update info.json
    try:
        with open(info_file, 'r') as f:
            info = json.load(f)
        
        info['total_episodes'] = len(episodes)
        info['splits'] = {"train": f"0:{len(episodes)}"}
        
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"✅ Updated {info_file}")
        print(f"   total_episodes: {info['total_episodes']}")
        print(f"   splits: {info['splits']}")
        
    except Exception as e:
        print(f"❌ Error updating info.json: {e}")
        # Restore backups
        shutil.copy2(backup_episodes, episodes_file)
        shutil.copy2(backup_info, info_file)
        return False
    
    print(f"\n🎉 Successfully renumbered {len(episodes)} episodes starting from {start_episode}")
    print(f"📊 New episode range: {start_episode} to {start_episode + len(episodes) - 1}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Renumber episodes in a LeRobot dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start numbering from 0
    python custom_scripts/renumber_episodes.py --repo_id LBST/t06_pick_and_place --start_episode 0
    
    # Continue from episode 66
    python custom_scripts/renumber_episodes.py --repo_id LBST/t06_pick_and_place --start_episode 66
    
    # Preview changes without applying them
    python custom_scripts/renumber_episodes.py --repo_id LBST/t06_pick_and_place --start_episode 0 --dry-run
        """
    )
    
    parser.add_argument(
        "--repo_id",
        type=str,
        required=True,
        help="HuggingFace dataset repo ID (e.g., 'LBST/t06_pick_and_place')"
    )
    
    parser.add_argument(
        "--start_episode",
        type=int,
        default=0,
        help="Starting episode number (default: 0)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    
    args = parser.parse_args()
    
    print("🤖 LeRobot Episode Renumbering Tool")
    print("=" * 40)
    
    if args.start_episode < 0:
        print("❌ Error: start_episode must be >= 0")
        return 1
    
    success = renumber_episodes(
        repo_id=args.repo_id,
        start_episode=args.start_episode,
        dry_run=args.dry_run
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
