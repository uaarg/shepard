import json
import shutil
from pathlib import Path
from typing import Optional

from src.modules.slam.slam_playback_provider import SLAMPlaybackProvider
from src.modules.slam.slam_provider import SLAMProvider
from src.modules.slam.slam_recorder import SLAMRecorder


class RecordingManager:
    """
    Manages multiple SLAM recordings stored under a single directory.

    Each recording is a subdirectory with a metadata.json and a frames/ folder.
    """

    def __init__(self, recordings_dir: str = "recordings"):
        self._dir = Path(recordings_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def list_recordings(self) -> list[dict]:
        """Return metadata for all stored recordings, sorted by creation time."""
        recordings = []
        for path in sorted(self._dir.iterdir()):
            meta_path = path / "metadata.json"
            if path.is_dir() and meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                meta["name"] = path.name
                recordings.append(meta)
        return recordings

    def new_recorder(self, name: str, provider: SLAMProvider) -> SLAMRecorder:
        """Create a new recorder that wraps provider and saves to recordings/<name>."""
        path = self._dir / name
        if path.exists():
            raise FileExistsError(f"Recording '{name}' already exists")
        return SLAMRecorder(provider, str(path))

    def load_playback(self, name: str, loop: bool = False) -> SLAMPlaybackProvider:
        """Load a recording by name and return a playback provider."""
        path = self._dir / name
        if not path.exists():
            raise FileNotFoundError(f"Recording '{name}' not found in {self._dir}")
        return SLAMPlaybackProvider(str(path), loop=loop)

    def delete_recording(self, name: str):
        """Permanently delete a recording."""
        path = self._dir / name
        if not path.exists():
            raise FileNotFoundError(f"Recording '{name}' not found")
        shutil.rmtree(path)
        print(f"Deleted recording '{name}'")

    def print_summary(self, recording: Optional[dict] = None):
        """Print a summary table of all recordings, or one specific recording."""
        recordings = [recording] if recording else self.list_recordings()
        if not recordings:
            print("No recordings found.")
            return
        print(f"{'Name':<30} {'Frames':>8} {'Duration':>10} {'Created'}")
        print("-" * 70)
        for r in recordings:
            import datetime
            created = datetime.datetime.fromtimestamp(
                r.get("created_at", 0)
            ).strftime("%Y-%m-%d %H:%M")
            print(
                f"{r['name']:<30} "
                f"{r.get('frame_count', '?'):>8} "
                f"{r.get('duration_sec', 0):>9.1f}s "
                f"{created}"
            )
