import curses
import time
import statistics
from datetime import datetime
from src.modules.autopilot.altimeter import XM125, SensorError


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
                screen.addstr(status_y, 8, f"Measurements: {measurement_count} | Errors: {error_count}")

                # Current readings section
                readings_y = 5
                screen.addstr(readings_y, 0, "Current Readings:", curses.A_BOLD)

                if peaks:
                    for i, peak_data in enumerate(peaks):
                        raw_distance, raw_strength = peak_data['raw']

                        # Add to history for statistics
                        distance_history.append(raw_distance)
                        if len(distance_history) > MAX_HISTORY:
                            distance_history.pop(0)

                        # Display current reading
                        screen.addstr(readings_y + i + 1, 2,
                                      f"Peak {i}: Distance = {raw_distance:5d}mm, Strength = {raw_strength:6d}")

                        if peak_data['averaged']:
                            avg_distance, avg_strength = peak_data['averaged']
                            screen.addstr(readings_y + i + 1, 45,
                                          f"Avg: {avg_distance:5.1f}mm, {avg_strength:6.1f}")
                else:
                    screen.addstr(readings_y + 1, 2, "No peaks detected", curses.color_pair(2))

                # Statistics section
                stats_y = readings_y + 6
                screen.addstr(stats_y, 0, "Statistics:", curses.A_BOLD)

                if distance_history:
                    mean_dist = statistics.mean(distance_history)
                    if len(distance_history) > 1:
                        stdev_dist = statistics.stdev(distance_history)
                    else:
                        stdev_dist = 0
                    min_dist = min(distance_history)
                    max_dist = max(distance_history)

                    screen.addstr(stats_y + 1, 2, f"Mean Distance: {mean_dist:.1f}mm")
                    screen.addstr(stats_y + 2, 2, f"Std Dev: {stdev_dist:.1f}mm")
                    screen.addstr(stats_y + 3, 2, f"Min: {min_dist}mm")
                    screen.addstr(stats_y + 4, 2, f"Max: {max_dist}mm")

                # Help text
                screen.addstr(height - 1, 0, "Press 'q' to quit", curses.A_DIM)

                screen.refresh()

                # Check for quit command
                c = screen.getch()
                if c == ord('q'):
                    break

                time.sleep(0.1)

            except SensorError as e:
                error_count += 1
                screen.addstr(height - 2, 0, f"Sensor error: {e}", curses.color_pair(3))
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
