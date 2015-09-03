A simple example file-set
=========================

This set of files describes a trivial SpiNNaker application consisting of three
vertices, `vertex0`, `vertex1` and  `vertex2`. These vertices are connected by
two nets as follows:

         net 1, weight 1.0
        _________  ________
       /         \/        \
       |          |        |
      \|/         |       \|/
    vertex0    vertex1   vertex2
     | /|\
     |  |
     \__/
     net 0, weight 1.0

The machine they are placed onto is a single 48-chip SpiNN-5 board with 18
working cores on all chips and no dead links.

A constraint ensures that core 0 on every chip in the system is not used (since
it is the monitor processor). A further constraint forces `vertex0` to be
placed on chip (2, 2).

The placement and allocation described places `vertex0` on core 1 of (2, 2), as
per the constraint, and `vertex1` and `vertex2` on cores 1 and 2 of chip (0, 0)
respectively.

Net 0 is routed directly back to its sending core (core 0). Net 1 is routed to
core 2 of chip (0, 0) and via a straight-line path to core 1 of (2, 2) via chip
(1, 1).

Net 0 is assigned a key of 1 and net 1 is assigned a key of 2. Both keys are
masked to the full 32-bits of the routing key.

The routing tables generated are straightforward with routing entries only
being present on chips (0, 0) and (2, 2).
