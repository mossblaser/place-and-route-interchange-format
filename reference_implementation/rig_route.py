#!/usr/bin/env python

"""
A script which uses a routing algorithm from Rig to route a placed and
allocated netlist supplied in JSON format.
"""

import logging

import json

import argparse

from six import iteritems

from importlib import import_module

from rig.routing_table import Routes
from rig.place_and_route.routing_tree import RoutingTree

from common import unpack_graph, unpack_machine, unpack_constraints, \
    unpack_placements, unpack_allocations, route_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Route a JSON netlist using rig's routing algorithms.")

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
                        help="a JSON file into which to write the routes")
    parser.add_argument("--core-resource", "-C", default="cores",
                        help="the name of the 'core' resource type "
                             "(default: %{default})")
    parser.add_argument("--algorithm", "-A",
                        help="the routing algorithm to use")
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

    allocations_json = []
    for resource_filename in args.allocations:
        resource, _, filename = resource_filename.partition(":")
        with open(filename, "r") as f:
            allocation_json = json.load(f)
            assert allocation_json["type"] == resource
            allocations_json.append(allocation_json)
    allocations = unpack_allocations(allocations_json)

    if args.algorithm:
        try:
            module = "rig.place_and_route.route.{}".format(args.algorithm)
            router = getattr(import_module(module), "route")
        except (ImportError, AttributeError):
            parser.error(
                "Unknown routing algorithm '{}'".format(args.algorithm))
    else:
        # Use default router
        import rig.place_and_route.route as router

    routes = router(vertices_resources, nets, machine, constraints,
                    placements, allocations,
                    core_resource=args.core_resource)

    def routing_tree_to_json(node):
        return {
            "chip": node.chip,
            "children": [
                {
                    "route": (route_name(route)
                              if isinstance(route, Routes)
                              else route),
                    "next_hop": (routing_tree_to_json(obj)
                                 if isinstance(obj, RoutingTree)
                                 else obj)
                }
                for route, obj in node.children
            ]
        }

    with open(args.routes, "w") as f:
        json.dump({
            name: routing_tree_to_json(routes[net])
            for net, name in iteritems(net_names)
        }, f)
