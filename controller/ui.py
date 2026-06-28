from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text


console = Console()


def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="top", size=3),
        Layout(name="body"),
        Layout(name="bottom", size=10),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )
    return layout


class Dashboard:
    def __init__(self):
        self.layout = build_layout()
        self.log_lines = []
        self.current_image = "-"
        self.current_diagnosis = {}
        self.current_telemetry = {}
        self.last_gcode = []
        self.loop_count = 0
        self.loop_time = 0
        self.camera_total = 0

    def update_status(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append(f"[{timestamp}] {message}")
        if len(self.log_lines) > 20:
            self.log_lines = self.log_lines[-20:]

    def _render_header(self):
        return Panel(
            Text("CortexFDM - AI Closed-Loop 3D Printer Monitor", style="bold cyan"),
            style="white",
        )

    def _render_left(self):
        defect = self.current_diagnosis.get("defect_type", "-")
        action = self.current_diagnosis.get("action_required", "-")

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="yellow", width=14)
        table.add_column("Value", style="white")

        table.add_row("Image", self.current_image)
        table.add_row("Frame", f"{self.loop_count % max(self.camera_total, 1) + 1}/{self.camera_total}")
        table.add_row("Defect", defect)
        table.add_row("Action", action)
        table.add_row("Loop", f"#{self.loop_count}")
        table.add_row("Time", f"{self.loop_time:.1f}s" if self.loop_time else "-")

        return Panel(table, title="Camera & Diagnosis", border_style="green")

    def _render_right(self):
        temp = self.current_telemetry
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="yellow", width=14)
        table.add_column("Value", style="white")

        if temp:
            table.add_row("E-Temp", f"{temp.get('extruder_target', '-')}C (target: {temp.get('extruder_actual', '-')}C)")
            table.add_row("B-Temp", f"{temp.get('bed_target', '-')}C (target: {temp.get('bed_actual', '-')}C)")
            table.add_row("Pos X", str(temp.get("position_x", "-")))
            table.add_row("Pos Y", str(temp.get("position_y", "-")))
            table.add_row("Pos Z", str(temp.get("position_z", "-")))
        else:
            table.add_row("Status", "Not connected")

        gcode_text = " | ".join(self.last_gcode) if self.last_gcode else "-"
        table.add_row("G-code", gcode_text[:40])

        return Panel(table, title="Printer Telemetry", border_style="blue")

    def _render_logs(self):
        lines = self.log_lines[-8:]
        text = "\n".join(lines) if lines else "Waiting for events..."
        return Panel(text, title="Event Log", border_style="magenta")

    def render(self):
        self.layout["top"].update(self._render_header())
        self.layout["left"].update(self._render_left())
        self.layout["right"].update(self._render_right())
        self.layout["bottom"].update(self._render_logs())
        return self.layout
