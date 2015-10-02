#!/usr/bin/env python

"""
A script which uses an allocation algorithm from Rig to allocate a placed
netlist supplied in JSON format.
"""

import logging

import json

import argparse

from six import iteritems

from importlib import import_module

from common import unpack_graph, unpack_machine, unpack_constraints, \
    unpack_placements


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Allocate a JSON netlist using "
                    "rig's allocation algorithms.")

    parser.add_argument("--graph", "-g", required=True,
                        help="a JSON file describing the problem graph")
    parser.add_argument("--machine", "-m", required=True,
                        help="a JSON file describing the SpiNNaker machine")
    parser.add_argument("--constraints", "-c", required=True,
                        help="a JSON file describing the constraints")
    parser.add_argument("--placements", "-p", required=True,
                        help="a JSON file describing the placements")
    parser.add_argument("--allocations-prefix", "-a", required=True,
                        help="prefix for allocation filenames")
    parser.add_argument("--algorithm", "-A",
                        help="the allocation algorithm to use")
    parser.add_argument("--verbose", "-v", action="count", default=0,
                        help="verbosity level (may be given multiple times)")
    args = parser.parse_args()

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)

    with open(args.graph, "r") as f:
        vertices_resources, nets, net_names = unpack_graph(json.load(f))

    with open(args.machine, "r") as f:
        machine = unpack_machine(json.load(f))

    with open(args.constraints, "r") as f:
        constraints = unpack_constraints(json.load(f))

    with open(args.placements, "r") as f:
        placements = unpack_placements(json.load(f))

    if args.algorithm:
        try:
            module = "rig.place_and_route.allocate.{}".format(args.algorithm)
            allocator = getattr(import_module(module), "allocate")
        except (ImportError, AttributeError):
            parser.error(
                "Unknown allocation algorithm '{}'".format(args.algorithm))
    else:
        # Use default allocator
        import rig.place_and_route.allocate as allocator

    allocations = allocator(vertices_resources, nets, machine, constraints,
                            placements)

    for resource in machine.chip_resources:
        with open("{}{}.json".format(args.allocations_prefix, resource),
                  "w") as f:
            json.dump({
                "type": resource,
                "allocations": {
                    v: [a[resource].start, a[resource].stop]
                    for v, a in iteritems(allocations)
                    if resource in a and a[resource].start != a[resource].stop
                }
            }, f)
