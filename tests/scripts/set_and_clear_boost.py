"""Exercise boost on a real Flux Go unit and check both fan speeds."""

import argparse
import ipaddress
import sys
import time
from pathlib import Path


# Import the API module without importing the Home Assistant component package.
COMPONENT_DIR = Path(__file__).resolve().parents[2] / "custom_components" / "renson_fluxgo"
sys.path.insert(0, str(COMPONENT_DIR))
from api import FluxGoApi  # noqa: E402


def ip_address(value: str) -> str:
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def read_rpms(api: FluxGoApi, stage: str) -> tuple[float, float]:
    sensors = api.get("/decision/sensor_values")
    extract = float(sensors["exhaust_fan_rpm"])
    supply = float(sensors["supply_fan_rpm"])
    print(f"{stage}: extract={extract:.0f} RPM, supply={supply:.0f} RPM")
    return extract, supply


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set 100% boost for 900 seconds, then clear it and check fan RPMs."
    )
    parser.add_argument("ip_address", type=ip_address, help="Ventilation unit IP address")
    parser.add_argument("api_key", help="Ventilation unit API key")
    args = parser.parse_args()

    api = FluxGoApi(args.ip_address, args.api_key)
    api.verify_token()

    print("Setting 100% boost on extract and supply for 900 seconds.", flush=True)
    try:
        api.set_boost(level=100, minutes=15)
        time.sleep(60)
        boosted = read_rpms(api, "Boosted")
    finally:
        print("Clearing boost on extract and supply.", flush=True)
        api.set_boost(level=20, minutes=1)

    time.sleep(60)
    cleared = read_rpms(api, "Cleared")

    if any(rpm <= 2000 for rpm in boosted):
        raise AssertionError(f"Boosted RPMs must both be above 2000: {boosted}")
    if any(rpm >= 1500 for rpm in cleared):
        raise AssertionError(f"Cleared RPMs must both be below 1500: {cleared}")
    print("Both RPM checks passed.")


if __name__ == "__main__":
    main()
