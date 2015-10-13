#!/usr/bin/env python

"""
A script which converts a given graph into a rig-compatible pickled netlist for
use with rig-par-diagram.
"""

import json

import pickle

import argparse

from six import iteritems

from common import unpack_graph, unpack_machine, unpack_constraints, \
    unpack_placements, unpack_allocations, unpack_routes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate pickled Rig netlists from a set of JSON files")

    parser.add_argument("output",
                        help="the file to write the netlist to")
    parser.add_argument("--graph", "-g", required=True,
                        help="a JSON file describing the problem graph")
    parser.add_argument("--machine", "-m", required=True,
                        help="a JSON file describing the SpiNNaker machine")
    parser.add_argument("--constraints", "-c", required=True,
                        help="a JSON file describing the constraints")
    parser.add_argument("--placements", "-p", required=True,
                        help="a JSON file describing the placements")
    parser.add_argument("--allocations", "-a", required=True, action="append",
                        help="Allocation filenames in the form "
                        "resource:filneame. Must be given once for each "
                        "resource type.")
    parser.add_argument("--routes", "-r", required=True,
                        help="a JSON file describing the routes")
    args = parser.parse_args()

    with open(args.graph, "r") as f:
        vertices_resources, nets, net_names = unpack_graph(json.load(f))
    name_nets = {name: net for net, name in iteritems(net_names)}

    with open(args.machine, "r") as f:
        machine = unpack_machine(json.load(f))

    with open(args.constraints, "r") as f:
        constraints = unpack_constraints(json.load(f))

    with open(args.placements, "r") as f:
        placements = unpack_placements(json.load(f))

    allocations_json = []
    for resource_filename in args.allocations:
        resource, _, filename = resource_filename.partition(":")
        with open(filename, "r") as f:
            allocation_json = json.load(f)
            assert allocation_json["type"] == resource
            allocations_json.append(allocation_json)
    allocations = unpack_allocations(allocations_json)

    with open(args.routes, "r") as f:
        routes = unpack_routes(json.load(f))

    routes = {name_nets[name]: route for name, route in iteritems(routes)}

    with open(args.output, "wb") as f:
        pickle.dump({
            "vertices_resources": vertices_resources,
            "nets": nets,
            "machine": machine,
            "constraints": constraints,
            "placements": placements,
            "allocations": allocations,
            "routes": routes,
            "core_resource": "cores",
        }, f)
