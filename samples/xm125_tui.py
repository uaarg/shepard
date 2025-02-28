# xm125_tui.py
import curses
import time
import statistics
from datetime import datetime
from src.modules.autopilot.altimeter_xm125 import XM125, SensorError


def format_measurement_table(screen, start_y, peaks, width):
    """Format measurements in a clean table layout"""
    # Table headers
    screen.addstr(start_y, 0, "Raw Measurements:", curses.A_BOLD)
    screen.addstr(start_y, width // 2, "Averaged Measurements:", curses.A_BOLD)

    # Column headers for raw data
    screen.addstr(start_y + 1, 2, "Peak │ Distance (mm) │ Strength", curses.A_DIM)
    screen.addstr(start_y + 2, 2, "─────┼──────────────┼──────────", curses.A_DIM)

    # Column headers for averaged data
    screen.addstr(start_y + 1, width // 2 + 2, "Peak │ Distance (mm) │ Strength", curses.A_DIM)
    screen.addstr(start_y + 2, width // 2 + 2, "─────┼──────────────┼──────────", curses.A_DIM)

    if peaks:
        for i, peak_data in enumerate(peaks):
            raw_distance, raw_strength = peak_data['raw']

            # Raw data
            raw_line = f" {i:3d} │ {raw_distance:>12d} │ {raw_strength:>8d}"
            screen.addstr(start_y + 3 + i, 2, raw_line)

            # Averaged data if available
            if peak_data['averaged']:
                avg_distance, avg_strength = peak_data['averaged']
                avg_line = f" {i:3d} │ {avg_distance:>12.1f} │ {avg_strength:>8.1f}"
                screen.addstr(start_y + 3 + i, width // 2 + 2, avg_line)
    else:
        screen.addstr(start_y + 3, 2, "No peaks detected", curses.color_pair(2))

    return start_y + 5 + (len(peaks) if peaks else 1)


def tui_main():
    def setup_curses():
        screen = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
        screen.nodelay(1)
        return screen

    def cleanup_curses(screen):
        screen.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    try:
        screen = setup_curses()
        sensor = XM125(average_window=10)

        # Statistics tracking
        distance_history = []
        MAX_HISTORY = 100
        error_count = 0
        measurement_count = 0
        start_time = datetime.now()

        if not sensor.begin():
            cleanup_curses(screen)
            print("Failed to initialize sensor")
            return

        while True:
            try:
                screen.clear()
                height, width = screen.getmaxyx()

                # Header
                runtime = datetime.now() - start_time
                header = f"XM125 Radar Sensor Monitor - Runtime: {runtime}"
                screen.addstr(0, 0, header, curses.A_BOLD)
                screen.addstr(1, 0, "=" * width)

                # Get measurement
                peaks = sensor.measure()
                measurement_count += 1

                # Status section
                status_y = 3
                screen.addstr(status_y, 0, "Status:", curses.A_BOLD)
                status_info = [
                    f"Measurements: {measurement_count}",
                    f"Errors: {error_count}",
                    f"Sample Rate: {1000 / 100:.1f} Hz"  # Assuming 100ms sleep
                ]
                for i, info in enumerate(status_info):
                    screen.addstr(status_y, 15 + i * 25, info)

                # Measurements section
                readings_y = 5
                next_y = format_measurement_table(screen, readings_y, peaks, width)

                # Update history and calculate statistics
                if peaks and peaks[0]['raw'][0]:  # Use first peak for statistics
                    distance_history.append(peaks[0]['raw'][0])
                    if len(distance_history) > MAX_HISTORY:
                        distance_history.pop(0)

                # Statistics section
                stats_y = next_y + 1
                screen.addstr(stats_y, 0, "Statistics:", curses.A_BOLD)

                if distance_history:
                    mean_dist = statistics.mean(distance_history)
                    if len(distance_history) > 1:
                        stdev_dist = statistics.stdev(distance_history)
                    else:
                        stdev_dist = 0
                    min_dist = min(distance_history)
                    max_dist = max(distance_history)

                    stats_data = [
                        f"Mean: {mean_dist:.1f}mm",
                        f"Std Dev: {stdev_dist:.1f}mm",
                        f"Min: {min_dist}mm",
                        f"Max: {max_dist}mm",
                        f"Samples: {len(distance_history)}"
                    ]

                    for i, stat in enumerate(stats_data):
                        screen.addstr(stats_y + 1, 2 + i * 20, stat)

                # Help section
                help_y = height - 2
                help_text = [
                    ("q", "Quit"),
                    ("r", "Reset Statistics")
                ]
                screen.addstr(help_y, 0, "Commands:", curses.A_DIM)
                for i, (key, desc) in enumerate(help_text):
                    screen.addstr(help_y, 12 + i * 20, f"{key}: {desc}", curses.A_DIM)

                screen.refresh()

                # Check for quit command
                c = screen.getch()
                if c == ord('q'):
                    break
                elif c == ord('r'):
                    distance_history.clear()

                time.sleep(0.1)

            except SensorError as e:
                error_count += 1
                screen.addstr(height - 3, 0, f"Sensor error: {e}", curses.color_pair(3))
                screen.refresh()
                time.sleep(2.0)
                continue

    except KeyboardInterrupt:
        pass
    except Exception as e:
        cleanup_curses(screen)
        print(f"Fatal error: {e}")
    finally:
        cleanup_curses(screen)
        sensor.bus.close()


if __name__ == "__main__":
    tui_main()
