#!/usr/bin/env python

"""
A script which uses a placement algorithm from Rig to place a netlist supplied
in JSON format.
"""

import logging

import json

import argparse

from importlib import import_module

from six import itervalues

from rig.netlist import Net
from rig.machine import Machine, Links
from rig.place_and_route.constraints import \
    LocationConstraint, ReserveResourceConstraint, RouteEndpointConstraint, \
    SameChipConstraint


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Place a JSON netlist using rig's placement algorithm.")

    parser.add_argument("graph",
                        help="a JSON file describing the problem graph")
    parser.add_argument("machine",
                        help="a JSON file describing the SpiNNaker machine")
    parser.add_argument("constraints", nargs='?',
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
        graph = json.load(f)
        vertices_resources = graph["vertices_resources"]
        nets = [
            Net(edge["source"], edge["sinks"], edge["weight"])
            for edge in itervalues(graph["edges"])
        ]

    with open(args.machine, "r") as f:
        machine_json = json.load(f)
        link_lookup = {l.name: l for l in Links}
        machine = Machine(width=machine_json["width"],
                          height=machine_json["height"],
                          chip_resources=machine_json["chip_resources"],
                          chip_resource_exceptions={
                              (x, y): {resource: r.get(resource, 0)
                                       for resource
                                       in machine_json["chip_resources"]}
                              for x, y, r
                              in machine_json["chip_resource_exceptions"]},
                          dead_chips=set((x, y)
                                         for x, y
                                         in machine_json["dead_chips"]),
                          dead_links=set((x, y, link_lookup[link])
                                         for x, y, link
                                         in machine_json["dead_links"]))

    constraints = []
    if args.constraints:
        with open(args.constraints, "r") as f:
            for json_constraint in json.load(f):
                if json_constraint["type"] == "location":
                    constraints.append(
                        LocationConstraint(json_constraint["vertex"],
                                           tuple(json_constraint["location"])))
                elif json_constraint["type"] == "reserve_resource":
                    constraints.append(
                        ReserveResourceConstraint(
                            json_constraint["resource"],
                            slice(*json_constraint["reservation"]),
                            (tuple(json_constraint["location"])
                             if json_constraint.get("location") is not None
                             else None)))
                elif json_constraint["type"] == "route_endpoint":
                    constraints.append(
                        RouteEndpointConstraint(
                            json_constraint["vertex"],
                            link_lookup[json_constraint["route"]]))
                elif json_constraint["type"] == "same_chip":
                    constraints.append(
                        SameChipConstraint(
                            json_constraint["vertices"]))
                else:
                    logging.warning(
                        "Unsupported constraint type '{}'".format(
                            json_constraint["type"]))

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
