#!/usr/bin/env python3
"""
Headless automation example: Full automated workflow without GUI.

This example shows how to:
1. Launch the app in headless mode
2. Run measurements programmatically
3. Properly shut down when done
"""

import time
from pathlib import Path
from pyonoy import (
    Absorbance96Client,
    ConnectionConfig,
    ExportFormat,
    SiLAConfig,
    launch_sila_server,
)


def run_automated_workflow():
    """Run a fully automated measurement workflow."""

    # Configuration - protocol is in same directory as this script
    SCRIPT_DIR = Path(__file__).parent.resolve()
    PROTOCOL = (SCRIPT_DIR / "absorbance_600.byop").as_uri()
    OUTPUT_DIR = SCRIPT_DIR / "results"
    SERVER_PORT = 50051

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Launch the application in headless mode
    print("Launching Absorbance 96 App in headless mode...")
    sila_config = SiLAConfig(
        port=SERVER_PORT,
        ip="0.0.0.0",
        insecure=True,  # Use TLS in production
        headless=False,
    )

    process = launch_sila_server(sila_config)
    print(f"Started with PID: {process.pid}")

    # Connect to the server
    client = Absorbance96Client(ConnectionConfig(
        port=SERVER_PORT,
        insecure=True,
    ))

    try:
        print("Waiting for server startup...")
        client.connect()
        print("Connected to SiLA2 server")

        print(f"Loading protocol: {PROTOCOL}")
        client.load_workspace(PROTOCOL)

        print("Preparing reader...")
        client.prepare_for_readout()

        # In a real automation scenario, you might signal a robot
        # to insert the plate here instead of waiting for user input
        print("READY FOR PLATE INSERTION")
        # robot.insert_plate()  # hypothetical robot control
        time.sleep(2)  # Simulate plate insertion time

        print("Performing readout...")
        client.perform_readout()

        # Signal plate removal
        print("READY FOR PLATE REMOVAL")
        # robot.remove_plate()  # hypothetical robot control
        time.sleep(2)  # Simulate plate removal time

        # Export results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"results_{timestamp}.csv"

        results = client.get_results(format=ExportFormat.CSV)
        output_file.write_bytes(results)
        print(f"Results saved: {output_file}")

        # Shut down the headless application
        print("Shutting down application...")
        client.quit_application()

    except Exception as e:
        print(f"Error during workflow: {e}")
        # Try to terminate the process if something goes wrong
        process.terminate()
        raise

    finally:
        client.disconnect()

    print("Workflow complete!")


if __name__ == "__main__":
    run_automated_workflow()
