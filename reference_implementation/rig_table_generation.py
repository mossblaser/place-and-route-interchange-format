#!/usr/bin/env python

"""
A script which uses a routing table generator from Rig to generate routing
tables from a supplied set of routes.
"""

import logging

import json

import argparse

from six import iteritems

from rig.place_and_route.utils import build_routing_tables

from common import unpack_routes, unpack_net_keys, route_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate routing tables from JSON routes and keys.")

    parser.add_argument("--routes", "-r", required=True,
                        help="a JSON file describing the routes")
    parser.add_argument("--routing-keys", "-k", required=True,
                        help="a JSON file describing the keys for each net")
    parser.add_argument("--routing-tables", "-t", required=True,
                        help="a JSON file to write the routing tables to")
    parser.add_argument("--keep-default-routes", "-K", action="store_true",
                        help="do not remove default routes from tables")
    parser.add_argument("--verbose", "-v", action="count", default=0,
                        help="verbosity level (may be given multiple times)")
    args = parser.parse_args()

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)

    with open(args.routes, "r") as f:
        routes = unpack_routes(json.load(f))
    with open(args.routing_keys, "r") as f:
        net_keys = unpack_net_keys(json.load(f))

    tables = build_routing_tables(routes,
                                  net_keys,
                                  not args.keep_default_routes)

    with open(args.routing_tables, "w") as f:
        json.dump([
            {
                "chip": xy,
                "entries": [
                    {
                        "key": entry.key,
                        "mask": entry.mask,
                        "directions": [route_name(r) for r in entry.route]
                    }
                    for entry in entries
                ]
            }
            for xy, entries in iteritems(tables)
        ], f)
