# socialsimullm/__main__.py

# -*- coding: utf-8 -*-

"""
CLI entry point for SocialSimuLLM.

Usage:
    uv run socialsimullm --project <name> [--steps N] [--model <model>]

@author: Huang Miaosen
"""

from socialsimullm.utils.config import load_config
from socialsimullm.simulator.core import SimulatorCore


def main() -> None:
    """Parse CLI arguments and run the simulation."""
    config = load_config()
    simulator = SimulatorCore(config)
    simulator.initialize()
    simulator.run(max_steps=config.max_steps)


if __name__ == "__main__":
    main()
