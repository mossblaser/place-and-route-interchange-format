Place & Route Data Interchange Format
=====================================

The task of mapping graph-like applications onto specific cores in a SpiNNaker
machine and defining routes between them is broadly split into these steps:

* **Placement**: Assign each graph vertex to a chip.
* **Allocation**: Allocate specific chip resources to each vertex (e.g. cores,
  memory).
* **Routing**: Generate routes to connect vertices according to a supplied set
  of nets.
* **Key Allocation**: Generate routing keys for each routed net.
* **Routing Table Generation**: Generate routing tables.

Terminology
-----------

The key pieces of terminology used are defined below:

Application Graph
:   The [hyper-graph](http://en.wikipedia.org/wiki/Hypergraph) which describes
    how an application's computational resources (the *vertices*) are connected
    to each other by *nets*.

Vertex
:   A *vertex* in an *application graph*. Each vertex is mapped onto exactly one
    SpiNNaker chip by during the placement process. (Note: an individual
    SpiNNaker chip may have several *vertices* mapped to it but each vertex
    will be mapped to exactly one chip). Each vertex consumes a certain set of
    *resources*. In most applications a vertex consume a single SpiNNaker core
    and a some SDRAM.
    
    *Vertices* are uniquely identified by a (short) unique string.

Net
:   A (directed) connection from one *vertex* to a number of other *vertices*
    in the *application graph*. During routing, nets are converted into
    specific routes through a SpiNNaker machine which can be used to generate
    routing tables. A net may also have a (positive) weight associated with it
    which may be used as a hint by placement and routing algorithms.

Resource
:   A *resource* is any finite resource available to a SpiNNaker chip (e.g.
    cores, SDRAM) which may be consumed by a vertex. *Resources* are allocated
    to each *vertex* during allocation. Each resource type is identified by a
    (short) unique string.
    
    The following standard chip resources are defined by convention but other
    resource types may be defined at will.
    
    * **"cores"**: SpiNNaker cores (including both monitor and application
      cores) on a chip. Most vertices are allocated one of these.
    * **"sdram"**: SDRAM, as allocated by SARK/Spin-1 API from the heap.
      Measured in bytes.
    
    Quantities of a *resource* are represented by positive integer values.

Constraint
:   *Constraints* specify additional requirements on how an application graph is
    placed and routed. For example a constraint might be used to force a
    particular *vertex* to always be placed on a specific chip.

Machine
:   A description of a SpiNNaker machine whose topology is assumed to be a
    rectangular hexagonal toroid, possibly with some dead links/chips and some
    cores with differing levels of resources available.


Tool-flow
---------

A place/route problem and solution is broken down into various individual
algorithms. Initially, the following files are provided which describe the
problem:

* `vertices_resources.json`: Enumerates each vertex in the graph and the
  resources it consumes.
* `nets.json`: Enumerates the nets which connect those vertices together.
* `machine.json`: Describes a SpiNNaker machine (dimensions, available
  resources) into which the application must be mapped.
* `constraints.json`: Describes a set of constraints on how the application
  should be placed/routed etc.

These files are supplied to a placement algorithm which produces a new file:

* `placements.json`: For each vertex, gives the chip onto which it was placed.

After this, these files are supplied an allocation algorithm which produces a
further file:

* `allocations.json`: For each vertex, gives the chip resources allocated to
  it.

Next, these files are supplied to a routing algorithm which produces another
new file:

* `routes.json`: This file describes the route to be taken by each net.

A key-generation algorithm can be used to generate routing keys for each net in
the application, producing a new file:

* `keys.json`: For each net, gives the routing key and mask which will identify
  it.

A routing table generation algorithm combines the above files into routing
tables for chips in the machine:

* `routing_tables.json`: For each chip on which routing entries are required,
  the routing table entries are enumerated.

Tool authors are free to merge, break-apart and reorder any or all of these
steps. For example, authors may wish to combine key generation and table
generation. By respecting the format of these files, tools may (hopefully...)
be freely combined.


File Formats
------------

All files are encoded using [JSON](http://www.json.org/), a simple
human-readable, light-weight data-interchange format. High-performance JSON
libraries are available for all popular programming languages (and plenty of
unpopular ones too...). A complete example set of example files is provided in
the [`examples/simple`](./examples/simple) directory of this repository.

For each file type, a [schema is provided](./schemas) (written in [JSON
Schema](http://json-schema.org/)) which more formally defines the structure of
the data. You can automatically verify the structural correctness of a data
file against these schemas using [any of a number of
validators](http://json-schema.org/implementations.html) (we recommend
[jsonschema](https://github.com/Julian/jsonschema), a validator written Python
with a straight-forward command-line interface. For example, to validate one of
the example files:

    $ jsonschema -i examples/simple/machine.json schemas/machine.json


