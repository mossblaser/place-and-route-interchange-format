A Preliminary Reference Implementation
======================================

This implementation uses Rig's place and route facilities to perform place and
route via the supplied file formats. The implementation will at some point get
a full suite of tests and get pulled into Rig but for now it will live here...


Example usage:

    # Place the example netlist
    rig_place.py ../examples/simple/graph.json \
                 ../examples/simple/machine.json \
                 ../examples/simple/constraints.json \
                 > placements.json
    
    # Allocate the example netlist (note using the example placement, not the
    # one generated above).
    rig_allocate.py ../examples/simple/graph.json \
                    ../examples/simple/machine.json \
                    ../examples/simple/constraints.json \
                    ../examples/simple/placements.json \
                    allocations_

See the `--help` for each command for more details.

All commands accept an `--algorithm` argument which allows the user to chose
the algorithm to use rather than just using the Rig default.

See the following Rig documentation pages for a list of available algorithms:

* [Placers](http://rig.readthedocs.org/en/stable/place_and_route/placement_algorithms.html)
* [Allocators](http://rig.readthedocs.org/en/stable/place_and_route/allocation_algorithms.html)
* [Routers](http://rig.readthedocs.org/en/stable/place_and_route/routing_algorithms.html)

Note that the default placer (`sa`) can be quite slow. Try `hilbert` for a fast
but lower quality placement. If you are using the `sa` placer, try adding `-vv`
so that you can see the debug output from the algorithm as it runs.
