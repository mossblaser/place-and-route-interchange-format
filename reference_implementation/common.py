#!/usr/bin/env python

"""
Common routines for converting to/from Rig's datastructures and JSON.
"""

import logging

from six import iteritems

from rig.netlist import Net
from rig.machine import Machine, Links
from rig.place_and_route.constraints import \
    LocationConstraint, ReserveResourceConstraint, RouteEndpointConstraint, \
    SameChipConstraint


# A lookup from link name (string) to Links enum entry.
LINK_LOOKUP = {l.name: l for l in Links}


def unpack_graph(json_graph):
    """Get vertices_resources and nets out of a JSON graph."""
    vertices_resources = json_graph["vertices_resources"]
    net_names = {
        Net(edge["source"], edge["sinks"], edge["weight"]): name
        for name, edge in iteritems(json_graph["edges"])
    }
    nets = list(net_names)

    return vertices_resources, nets, net_names


def unpack_machine(json_machine):
    """Get a Machine out of a JSON machine."""
    return Machine(width=json_machine["width"],
                   height=json_machine["height"],
                   chip_resources=json_machine["chip_resources"],
                   chip_resource_exceptions={
                       (x, y): {resource: r.get(resource, 0)
                                for resource
                                in json_machine["chip_resources"]}
                       for x, y, r
                       in json_machine["chip_resource_exceptions"]},
                   dead_chips=set((x, y)
                                  for x, y
                                  in json_machine["dead_chips"]),
                   dead_links=set((x, y, LINK_LOOKUP[link])
                                  for x, y, link
                                  in json_machine["dead_links"]))


def unpack_constraints(json_constraints):
    """Get Rig constraints out of a JSON representation."""
    constraints = []
    for json_constraint in json_constraints:
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
                    LINK_LOOKUP[json_constraint["route"]]))
        elif json_constraint["type"] == "same_chip":
            constraints.append(
                SameChipConstraint(
                    json_constraint["vertices"]))
        else:
            logging.warning(
                "Unsupported constraint type '{}'".format(
                    json_constraint["type"]))
    return constraints


def unpack_placements(json_placements):
    """Get placements out of a JSON version."""
    return {v: (x, y) for v, (x, y) in iteritems(json_placements)}


def unpack_allocations(json_allocations):
    """Get allocations out of a JSON version.

    Note that this expects multiple JSON allocation files' contents enumerated
    in a list.
    """
    # XXX: Won't include vertices with no resources of any type...
    allocations = {}
    for json_allocation in json_allocations:
        resource = json_allocation["type"]
        for v, (s, e) in iteritems(json_allocation["allocations"]):
            a = allocations.setdefault(v, {})
            a[resource] = slice(s, e)

    return allocations
