#!/usr/bin/env python3
import argparse
import sys
import subprocess
import os
import json
from pathlib import Path
from typing import List, Any, Optional

from models.feedback import FeedbackEvent, FeedbackLabel


class FeedbackCLI:
    """Interactive feedback review CLI for operator validation."""

    @staticmethod
    def load_pending() -> List[FeedbackEvent]:
        """Load and validate pending events from feedback_pending.json."""
        path = Path("feedback_pending.json")
        if not path.exists():
            return []

        try:
            with open(path) as f:
                raw = json.load(f)
            if not isinstance(raw, list):
                return []
            return [FeedbackEvent.model_validate(e) for e in raw]
        except (json.JSONDecodeError, Exception):
            print("⚠️  Invalid pending store, cleared.")
            path.unlink(missing_ok=True)
            return []

    @staticmethod
    def save_processed(events: List[dict[str, Any]]) -> None:
        """Save processed events to feedback_processed.json."""
        Path("feedback_processed.json").write_text(
            json.dumps(events, separators=(",", ":"))
        )

    @staticmethod
    def review_interactive() -> None:
        """Main interactive review loop for operator feedback."""
        pending = FeedbackCLI.load_pending()
        if not pending:
            print("✅ No pending feedback events.")
            return

        print(f"\n📋 {len(pending)} pending events found:\n")

        for i, event in enumerate(pending, 1):
            print(f"\n{i}. Fault: {event.fault_id}")
            print(f"   Type: {event.anomaly_type}")
            print(f"   Action: {event.recovery_action}")
            print(f"   Phase: {event.mission_phase}")
            print(f"   Time: {event.timestamp}")

            while True:
                label = (
                    input("\nLabel [correct/insufficient/wrong/q-uit]: ")
                    .strip()
                    .lower()
                )
                if label == "q":
                    sys.exit(0)
                try:
                    event.label = FeedbackLabel(label)
                    break
                except ValueError:
                    print("❌ Invalid: 'correct', 'insufficient', 'wrong'")

            notes = input("Notes (optional, Enter to skip): ").strip()
            if notes:
                event.operator_notes = notes

            print(f"✅ Saved: {event.label} - {event.fault_id}")

        # Save all processed by converting to JSON-safe dicts
        processed = [json.loads(e.model_dump_json()) for e in pending]
        FeedbackCLI.save_processed(processed)
        Path("feedback_pending.json").unlink(missing_ok=True)
        print(f"\n🎉 {len(pending)} events processed → ready for #53 pinning!")


def run_telemetry() -> None:
    subprocess.run(
        [sys.executable, os.path.join("astraguard", "telemetry", "telemetry_stream.py")]
    )


def run_dashboard() -> None:
    subprocess.run(["streamlit", "run", os.path.join("dashboard", "app.py")])


def run_simulation() -> None:
    subprocess.run([sys.executable, os.path.join("simulation", "attitude_3d.py")])


def run_classifier() -> None:
    subprocess.run([sys.executable, os.path.join("classifier", "fault_classifier.py")])


def run_logs(args: argparse.Namespace) -> None:
    cmd = [sys.executable, os.path.join("logs", "timeline.py")]
    if args.export:
        cmd.extend(["--export", args.export])
    subprocess.run(cmd)


def run_api(args: argparse.Namespace) -> None:
    cmd = [sys.executable, "run_api.py"]
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.reload:
        cmd.append("--reload")
    subprocess.run(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AstraGuard-AI: Unified CLI\nUse `cli.py <subcommand>`"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("telemetry", help="Run telemetry stream generator")
    subparsers.add_parser("dashboard", help="Run Streamlit dashboard UI")
    subparsers.add_parser("simulate", help="Run 3D attitude simulation")
    subparsers.add_parser("classify", help="Run fault classifier tests")
    logs_parser = subparsers.add_parser("logs", help="Event log utilities")
    logs_parser.add_argument(
        "--export",
        metavar="PATH",
        help="Export event log to file (same as logs/timeline.py)",
    )

    api_parser = subparsers.add_parser("api", help="Run REST API server")
    api_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    api_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    api_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    feedback_parser = subparsers.add_parser(
        "feedback", help="Operator feedback review interface"
    )
    feedback_parser.add_argument(
        "action",
        choices=["review"],
        help="Feedback action (review pending events)",
    )

    args = parser.parse_args()
    if args.command == "telemetry":
        run_telemetry()
    elif args.command == "dashboard":
        run_dashboard()
    elif args.command == "simulate":
        run_simulation()
    elif args.command == "classify":
        run_classifier()
    elif args.command == "logs":
        run_logs(args)
    elif args.command == "api":
        run_api(args)
    elif args.command == "feedback":
        if args.action == "review":
            FeedbackCLI.review_interactive()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
