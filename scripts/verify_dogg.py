from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "site" / "dogg" / "frames"
MANIFEST = ROOT / "site" / "dogg" / "manifest.json"
GENESIS = "0" * 64
FORBIDDEN_KEYS = {
    "api_token",
    "artifact_dir",
    "brief",
    "budget_usd",
    "context",
    "customer",
    "feedback",
    "problem",
    "prompt",
    "session_id",
}
FORBIDDEN_TEXT = (
    "/users/",
    ".brainstem",
    "api_token",
    "customer brief:",
)


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def safe(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden key at {path}.{key}")
            safe(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            safe(item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_TEXT):
            raise ValueError(f"forbidden text at {path}")


def verify() -> dict[str, Any]:
    paths = sorted(FRAMES.glob("*.json"))
    previous = GENESIS
    last_source = -1
    for expected, path in enumerate(paths):
        frame = json.loads(path.read_text(encoding="utf-8"))
        safe(frame)
        if frame.get("schema") != "rapterbot-public-dogg/1":
            raise ValueError(f"frame {expected} schema")
        if frame.get("seq") != expected:
            raise ValueError(f"frame {expected} sequence")
        if path.name != f"{expected:012d}.json":
            raise ValueError(f"frame {expected} filename")
        if frame.get("prev") != previous:
            raise ValueError(f"frame {expected} parent")
        if frame.get("payload_hash") != digest(frame.get("payload")):
            raise ValueError(f"frame {expected} payload hash")
        material = dict(frame)
        claimed = material.pop("frame_hash", None)
        if claimed != digest(material):
            raise ValueError(f"frame {expected} hash")
        if "source_seq" in frame:
            source_seq = int(frame["source_seq"])
            if source_seq <= last_source:
                raise ValueError(f"frame {expected} source sequence")
            last_source = source_seq
        previous = claimed
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    safe(manifest)
    if manifest.get("frame_count") != len(paths):
        raise ValueError("manifest frame count")
    if manifest.get("head") != previous:
        raise ValueError("manifest head")
    if paths:
        expected_latest = f"dogg/frames/{len(paths) - 1:012d}.json"
        if manifest.get("latest") != expected_latest:
            raise ValueError("manifest latest")
    return {"valid": True, "frames": len(paths), "head": previous}


def verify_append_only(base: str | None) -> None:
    if not base or set(base) == {"0"}:
        return
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            base,
            "HEAD",
            "--",
            "site/dogg/frames",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    invalid = [
        line
        for line in result.stdout.splitlines()
        if line and not line.startswith("A\t")
    ]
    if invalid:
        raise ValueError(
            "historical frame modification or deletion: " + ", ".join(invalid)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    args = parser.parse_args()
    verify_append_only(args.base)
    print(json.dumps(verify(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

