import asyncio
import logging
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from i2c_automation_agent.i2c_decoder.csv_reader import CsvFormatError, read_capture
from i2c_automation_agent.i2c_decoder.decoder import DecoderConfig, decode_capture
from i2c_automation_agent.i2c_decoder.export import (
    to_summary_rows,
    write_json,
    write_summary_csv,
    write_text,
)


logger = logging.getLogger(__name__)


class I2cBusyError(RuntimeError):
    pass


@dataclass
class I2cDecodeOptions:
    time_col: str | None = None
    scl_col: str | None = None
    sda_col: str | None = None
    scl_threshold: float | None = None
    sda_threshold: float | None = None
    hysteresis_fraction: float = 0.05


@dataclass
class I2cRun:
    run_id: str
    source_name: str
    input_path: Path
    output_dir: Path
    events: asyncio.Queue[dict[str, Any]]
    task: asyncio.Task | None = None
    sequence: int = 0


class I2cService:
    agent_id = "i2c-automation"

    def __init__(self) -> None:
        self._guard = asyncio.Lock()
        self._current_run: I2cRun | None = None
        self._status = "idle"
        self._workspace = Path(__file__).resolve().parents[2] / "i2c_automation_agent" / "workspace"
        self._input_dir = self._workspace / "uploads"
        self._runs_dir = self._workspace / "runs"

    @property
    def status(self) -> str:
        return self._status

    def prepare_upload_path(self, file_name: str | None) -> tuple[str, Path]:
        safe_name = self._safe_name(file_name or "capture.csv", "capture.csv")
        upload_dir = self._input_dir / uuid4().hex
        upload_dir.mkdir(parents=True, exist_ok=True)
        return safe_name, upload_dir / safe_name

    async def submit(
        self,
        input_path: Path,
        source_name: str,
        options: I2cDecodeOptions,
    ) -> str:
        async with self._guard:
            if self._current_run and self._current_run.task:
                if not self._current_run.task.done():
                    raise I2cBusyError("I2C Automation is currently decoding another capture")

            run_id = uuid4().hex
            output_dir = self._runs_dir / run_id
            output_dir.mkdir(parents=True, exist_ok=True)
            run = I2cRun(
                run_id=run_id,
                source_name=source_name,
                input_path=input_path,
                output_dir=output_dir,
                events=asyncio.Queue(),
            )
            self._current_run = run
            self._status = "running"
            run.task = asyncio.create_task(self._run_decode(run, options))
            return run.run_id

    def get_run(self, run_id: str) -> I2cRun | None:
        run = self._current_run
        return run if run and run.run_id == run_id else None

    def resolve_artifact(self, run_id: str, file_name: str) -> Path:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError("Run not found")
        safe_name = self._safe_name(file_name, "artifact")
        file_path = run.output_dir / safe_name
        if file_path.parent != run.output_dir or not file_path.is_file():
            raise ValueError("Artifact not found")
        return file_path

    def _event(self, run: I2cRun, event: dict[str, Any]) -> dict[str, Any]:
        run.sequence += 1
        return {
            "sequence": run.sequence,
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }

    async def _run_decode(self, run: I2cRun, options: I2cDecodeOptions) -> None:
        try:
            await run.events.put(self._event(run, {"type": "progress", "message": "Reading CSV capture"}))
            result = await asyncio.to_thread(self._decode_file, run, options)
            await run.events.put(
                self._event(
                    run,
                    {
                        "type": "completed",
                        "operation": "i2c_decode",
                        "answer": "I2C decode completed.",
                        **result,
                    },
                )
            )
        except (CsvFormatError, FileNotFoundError, ValueError) as exc:
            await run.events.put(self._event(run, {"type": "error", "message": str(exc)}))
        except Exception:
            logger.exception("I2C decode run %s failed", run.run_id)
            await run.events.put(
                self._event(
                    run,
                    {
                        "type": "error",
                        "message": "I2C decode failed. Check the server log.",
                    },
                )
            )
        finally:
            self._status = "idle"

    def _decode_file(self, run: I2cRun, options: I2cDecodeOptions) -> dict[str, Any]:
        raw = read_capture(
            run.input_path,
            time_col=self._blank_to_none(options.time_col),
            scl_col=self._blank_to_none(options.scl_col),
            sda_col=self._blank_to_none(options.sda_col),
        )
        decoded = decode_capture(
            raw,
            DecoderConfig(
                scl_threshold=options.scl_threshold,
                sda_threshold=options.sda_threshold,
                hysteresis_fraction=options.hysteresis_fraction,
            ),
        )

        stem = self._safe_stem(run.source_name)
        json_path = run.output_dir / f"{stem}.decoded.json"
        text_path = run.output_dir / f"{stem}.decoded.txt"
        csv_path = run.output_dir / f"{stem}.summary.csv"
        write_json(decoded, json_path)
        write_text(decoded, text_path)
        write_summary_csv(decoded, csv_path)

        artifacts = [
            self._artifact(run, "json", json_path),
            self._artifact(run, "text", text_path),
            self._artifact(run, "csv", csv_path),
        ]
        addresses = sorted(
            {txn.address_7bit for txn in decoded.transactions if txn.address_7bit is not None}
        )
        summary = {
            "source_file": run.source_name,
            "sample_count": decoded.capture.sample_count,
            "transactions": len(decoded.transactions),
            "complete": sum(1 for txn in decoded.transactions if txn.complete),
            "incomplete": sum(1 for txn in decoded.transactions if not txn.complete),
            "addresses": [f"0x{address:02X}" for address in addresses],
            "estimated_scl_frequency_hz": decoded.capture.estimated_scl_frequency_hz,
            "warnings": decoded.capture.warnings,
        }
        return {
            "summary": summary,
            "rows": to_summary_rows(decoded),
            "capture": asdict(decoded.capture),
            "artifacts": artifacts,
        }

    def _artifact(self, run: I2cRun, kind: str, path: Path) -> dict[str, str]:
        return {
            "kind": kind,
            "file_name": path.name,
            "download_url": (
                f"/api/agents/{self.agent_id}/runs/{run.run_id}/artifacts/"
                f"{quote(path.name)}"
            ),
        }

    @staticmethod
    def _safe_name(file_name: str, fallback: str) -> str:
        base_name = file_name.replace("\\", "/").rsplit("/", 1)[-1]
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._")
        return safe_name or fallback

    @classmethod
    def _safe_stem(cls, file_name: str) -> str:
        return Path(cls._safe_name(file_name, "capture.csv")).stem or "capture"

    @staticmethod
    def _blank_to_none(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


i2c_service = I2cService()