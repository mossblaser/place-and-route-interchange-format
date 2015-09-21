Place & Route Data Interchange Format
=====================================

The task of mapping graph-like applications onto specific cores in a SpiNNaker
machine and defining routes between them is broadly split into these steps:

* **Placement**: Assign each graph vertex to a chip.
* **Allocation**: Allocate specific chip resources to each vertex (e.g. cores,
  memory).
* **Routing**: Generate routes to connect vertices according to a supplied set
  of edges.
* **Routing Key Allocation**: Generate routing keys for each routed edge.
* **Routing Table Generation**: Generate routing tables.

Terminology
-----------

The key pieces of terminology used are defined below:

Application Graph
:   The [hyper-graph](http://en.wikipedia.org/wiki/Hypergraph) which describes
    how an application's computational resources (the *vertices*) are connected
    to each other by *edges*.

Vertex
:   A *vertex* in an *application graph*. Each vertex is mapped onto exactly one
    SpiNNaker chip by during the placement process. (Note: an individual
    SpiNNaker chip may have several *vertices* mapped to it but each vertex
    will be mapped to exactly one chip). Each vertex consumes a certain set of
    *resources*. In most applications a vertex consume a single SpiNNaker core
    and a some SDRAM.
    
    *Vertices* are uniquely identified by a (short) unique string.

Edge
:   A (directed) connection from one *vertex* to a number of other *vertices*
    in the *application graph*. During routing, edges are converted into
    specific routes through a SpiNNaker machine which can be used to generate
    routing tables. An edge may also have a (positive) weight associated with it
    which may be used as a hint by placement and routing algorithms. Finally,
    an edge may be labelled with a 'type' which may be interpreted by
    applications arbitrarily. For example, the type may indicate the type of
    SpiNNaker packet associated with the edge (e.g. multicast).

Resource
:   A *resource* is any finite resource available to a SpiNNaker chip (e.g.
    cores, SDRAM) which may be consumed by a vertex. *Resources* are allocated
    to each *vertex* during allocation. Each resource type is identified by a
    (short) unique string.
    
    The following standard chip resources are defined by convention but other
    resource types may be defined at will.
    
    * **"cores"**: SpiNNaker cores (including both monitor and application
      cores) on a chip. Most vertices are allocated exactly one of these.
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

* `graph.json`: Enumerates each vertex in the graph and the
  resources it consumes. Also enumerates the edges between the vertices.
* `machine.json`: Describes a SpiNNaker machine (dimensions, available
  resources) into which the application must be placed and routed.
* `constraints.json`: Describes a set of constraints on how the application
  should be placed/routed etc.

These files are supplied to a placement algorithm which produces a new file:

* `placements.json`: For each vertex, gives the chip onto which it was placed.

After this, these files are supplied an allocation algorithm which produces a
further file:

* `allocations.json`: For each vertex, gives the chip resources allocated to
  it. Optionally, allocations may be described seperately for each resource
  type in files named `allocations_resourcename.json`. The internal file format
  is identical.

Next, these files are supplied to a routing algorithm which produces another
new file:

* `routes.json`: This file describes the route to be taken by each edge.

A routing key-generation algorithm can be used to generate routing keys for
each edge in the application, producing a new file:

* `routing_keys.json`: For each edge, gives the multicast routing keys and
  masks which are associated with it. Edges which do not represent multicast
  routes may be omitted.

A routing table generation algorithm combines the above files into routing
tables for chips in the machine:

* `routing_tables.json`: For each chip on which routing entries are required,
  the routing table entries are enumerated.

Tool authors are free to merge, break-apart and reorder any or all of these
steps. For example, authors may wish to combine routing key generation and
routing table generation. By respecting the format of these files, tools may
(hopefully...) be freely combined.


Constraints
-----------

The following is an enumeration of the constraint types available:

* `location`: Force a specified vertex to always be placed on a certain chip.
* `resource`: Force a specified vertex to always consume a particular resource
  range on whichever chip it happens to be placed on.
* `reserve_resource`: Reserve a specific resource range on all or a specific
  chip.
* `route_endpoint`: Make sure that when routing to a particular vertex that the
  routes terminate on a particular link.
* `same_chip`: Make sure a set of vertices are always placed on the same chip
  together.
* `share_resources`: If any of a set of vertices are placed on the same
  chip, they may be allocated exactly overlapping resources. When placed on
  different chips however, they behave as usual. All vertices under this
  constraint must have identical resource requirements.
* `disjoint_routes`: Ensure selected groups of edges' routes never intersect
  eachother.

Some example uses:

* We have an external device connected to the west link of chip (0, 0)
  represented by the vertex `mydevice`.
  
  ```
  {
      "type": "location",
      "vertex": "mydevice",
      "location": [0, 0]
  },
  {
      "type": "route_endpoint",
      "vertex": "mydevice",
      "direction": "west"
  }
  ```

* We want to prevent core 0 being used because it is reserved for the monitor
  processor.
  
  ```
  {
      "type": "reserve_resource",
      "resource": "cores",
      "reservation": [0, 1]
  }
  ```

* We always want the vertex "specialSnowflake" to be allocated to core 3 of
  chip (1, 2).
  
  ```
  {
      "type": "location",
      "vertex": "specialSnowflake",
      "location": [1, 1]
  },
  {
      "type": "resource",
      "vertex": "specialSnowflake",
      "resource": "cores",
      "range": [3, 4]
  }
  ```

* We want the vertices "fred" and "bob" to always be placed on the same chip
  because they use some shared SDRAM.
  
  ```
  {
      "type": "same_chip",
      "vertices": ["fred", "bob"]
  }
  ```

* Say we have a block of memory which is common to two core-using vertices. If
  the vertices are placed on the same chip then we'd like just one copy of the
  memory block to be allocated to that chip. If the vertices are placed
  seperately, however, the vertices must have their own copies of the memory.
  
  We first define the core-using vertices, and the memory blocks they use, as
  follows:
  
  ```
  {
      "vertices_resources":{
          "v0": {"cores": 1},
          "m0": {"sdram": 1024},
          "v1": {"cores": 1},
          "m1": {"sdram": 1024},
      },
      ...
  }
  ```
  
  We then make sure that the SDRAM-representing vertices are always placed on
  the same chip as the associated core, and state that the memory resources may
  be shared.
  
  ```
  {
      "type": "same_chip",
      "vertices": ["v0", "m0"]
  },
  {
      "type": "same_chip",
      "vertices": ["v1", "m1"]
  },
  {
      "type": "share_resources",
      "vertices": ["m0", "m1"]
  }
  ```

* We have some fixed routes (`fr10`, `fr11` and `rf12`) which all terminate at
  the same vertex and we'd like to ensure these not to overlap with another set
  of fixed routes (`fr20` and `rf21`) whose paths must not overlap since that
  would result in a cyclic fixed route existing!
  
  ```
  {
      "type": "disjoint_routes",
      "edges": [
          ["fr10", "fr11", "fr12`],
          ["fr20", "fr21"]
      ]
  }
  ```


File Formats
------------

All files are encoded using [JSON](http://www.json.org/), a simple
human-readable, light-weight data-interchange format. High-performance JSON
libraries are available for all popular programming languages (and plenty of
unpopular ones too...).

### Examples

A complete example set of example files is provided in the
[`examples/simple`](./examples/simple) directory of this repository.

### Schemas

For each file type, a [schema is provided](./schemas) (written in [JSON
Schema](http://json-schema.org/)) which more formally defines the structure of
the data. You can automatically verify the structural correctness of a data
file against these schemas using [any of a number of
validators](http://json-schema.org/implementations.html) (we recommend
[jsonschema](https://github.com/Julian/jsonschema), a validator written Python
with a straight-forward command-line interface. For example, to validate one of
the example files:

    $ jsonschema -i examples/simple/machine.json schemas/machine.json


