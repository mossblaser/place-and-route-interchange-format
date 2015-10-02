#!/usr/bin/env python

"""
A script which uses a placement algorithm from Rig to place a netlist supplied
in JSON format.
"""

import logging

import json

import argparse

from importlib import import_module

from common import unpack_graph, unpack_machine, unpack_constraints


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Place a JSON netlist using rig's placement algorithms.")

    parser.add_argument("graph",
                        help="a JSON file describing the problem graph")
    parser.add_argument("machine",
                        help="a JSON file describing the SpiNNaker machine")
    parser.add_argument("constraints",
                        help="a JSON file describing the constraints")
    parser.add_argument("--algorithm", "-a",
                        help="the placement algorithm to use")
    parser.add_argument("--verbose", "-v", action="count", default=0,
                        help="verbosity level (may be given multiple times)")
    args = parser.parse_args()

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)

    with open(args.graph, "r") as f:
        vertices_resources, nets = unpack_graph(json.load(f))

    with open(args.machine, "r") as f:
        machine = unpack_machine(json.load(f))

    with open(args.constraints, "r") as f:
        constraints = unpack_constraints(json.load(f))

    if args.algorithm:
        try:
            module = "rig.place_and_route.place.{}".format(args.algorithm)
            placer = getattr(import_module(module), "place")
        except (ImportError, AttributeError):
            parser.error(
                "Unknown placement algorithm '{}'".format(args.algorithm))
    else:
        # Use default placer
        import rig.place_and_route.place as placer

    placements = placer(vertices_resources, nets, machine, constraints)

    print(json.dumps(placements))
