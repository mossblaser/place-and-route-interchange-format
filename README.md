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
algorithms:

* Placement -- Assigns each vertex to a chip.
* Allocation -- Assigns chip resources to each vertex.
* Routing -- Generates routes for each edge.
* Routing Table Generation/Compression -- Generates routing tables from a set
  of routes.

Tool authors are free to merge, break-apart and reorder any or all of these
steps. For example, authors may wish to combine routing key generation and
routing table generation. By respecting the format of these files, tools may
(hopefully...) be freely combined.

The following sections give an overview of the process including an informal
overview of the each of the file formats used to describe intermediate results.

### Describing the problem

Initially, the following files are provided which describe the problem and
machine into which it will be mapped:

#### `machine.json`

This file describes a SpiNNaker machine's topology and available resources. It
contains a JSON object which in a simple case looks like the following:

    {
        "width": 12
        "height": 12
        "chip_resources": {
            "cores": 18,
            "sdram": 119275520
        },
        "dead_chips": []
        "dead_links": []
        "chip_resource_exceptions": []
    }

The base assumption is that all machines consist of a rectangular array of
identical chips connected in a hexagonal torus, possibly with a few broken
chips, links and missing/differing resources on some chips.

The `width`, `height` and `chip_resources` members describe the dimensions of
the machine and the resources available on each core. The types of resources
may be application dependent but generally will include `cores` and `sdram`.
Note that `chip_resources` must enumerate every type of resource used anywhere,
even if most chips do not consume every resource type.

The `dead_chips` member enumerates any dead or missing chips in the machine in
the form of an array of two-element arrays of the form `[x, y]` giving the
coordinates of dead chips. For example:

    ...
    "dead_chips": [ [1, 0], [2, 4] ],
    ...

Indicates chips (1, 0) and (2, 4) are dead and may not be used.

The `dead_links` member enumerates any dead links in the machine in the form of
an array of three-element arrays of the form `[x, y, link]`. `x` and `y` give
the coordinates of the chip the dead link is sending from and `link` gives the
direction of the link and is one of `"north"`, `"north_east"`, `"east"`,
`"south"`, `"south_west"` and `"west"`. Note that all links in SpiNNaker
machines are bidirectional and each direction is considered separately so
*both* directions must be marked as dead to indicate both link directions are
dead. For example:

    ...
    "dead_links": [ [1, 1, "north"], [1, 2, "south"] ],
    ...

In this example both directions of the link between chips (1, 1) and (1, 2) are
marked as dead.

Finally, individual chips may have different quantities of certain resources,
for example, a different number of working cores. In this case all chips whose
resources differ from the rest must be enumerated in the
`chip_resource_exceptions` member which is an array of three-element arrays of
the form `[x, y, {"resource": quantity, ...}]`. Here `x` and `y` give the
coordinates of the chip whose resources differ and the JSON object enumerates
the differences in resources available on that chip compared with
`chip_resources`. Note that any resource type not listed in the exception will
be assumed to have the same value as defined in `chip_resources`:

    ...
    "chip_resource_exceptions": [
        [1, 1, {"cores": 17}],
        [2, 4, {"sdram": 0}],
    ]
    ...

In this example, chip (1, 1) has only 17 working cores (but a normal amount of
ram) and chip (2, 4) has no working SDRAM (but the normal 18 cores). All other
chips have the resources previously defined by `chip_resources`.

#### `graph.json`

This file enumerates the vertices and edges in the application graph which is
to be placed and routed. It contains a JSON object as follows:

    {
        "vertices_resources": {
            "vertex0": {"cores": 1},
            "vertex1": {"cores": 1, "sdram": 1024},
            "vertex2": {"cores": 1, "sdram": 1024}
        },
        "edges": {
            "edge0": {
                "source": "vertex0",
                "sinks": ["vertex0"],
                "weight": 1.0,
                "type": "mc"
            },
            "edge1": {
                "source": "vertex1",
                "sinks": ["vertex0", "vertex2"],
                "weight": 1.0,
                "type": "mc"
            }
        }
    }

Here the `vertices_resources` member enumerates the resources consumed by each
vertex in the problem. Vertices are uniquely identified by a user-defined
string. Each vertex must have its own unique name. The resources consumed by a
given vertex may be any subset of the resources defined in the machine
description.

The `edges` member enumerates any edges between vertices. Like vertices, edges
must be given a unique string which is used to uniquely identify each edge. An
edge is defined by a JSON object with four members as follows:

* `source`: The name of the vertex at the source of the edge.
* `sinks`: An array of vertices which are sinks of the edge.
* `weight`: A floating point number which is a hint to placement/routing
  algorithms indicating, e.g., the importance/traffic through a link. This may
  be set to `1.0` in applications which don't care.
* `type`: A user-defined string labelling the type of the edge. Used primarily
  as metadata and algorithms are free to ignore this field as they see fit. May
  be set to an empty string in applications which don't care.

#### `constraints.json`

This file contains a JSON array enumerating all the constraints applicable to
the supplied application. Constraints are defined by JSON objects and are more
fully defined in [the section describing the available
constraints](#Constraints).


### Placement Algorithms

Placement algorithms take the above files as arguments and (attempt to) produce
a set of placements which assigns each vertex to a specific chip in
`placements.json`.

#### `placements.json`

A single JSON object in which for each vertex, the (x, y) coordinates of the
chip it was placed on is given. For example:

    {
        "vertex0": [2, 2],
        "vertex1": [0, 0],
        "vertex2": [0, 0]
    }

### Allocation Algorithms

The allocation algorithm takes the above files as input and produces several
files named `allocations_resource.json`, one for each resource type allocated.
For example, if `cores` and `sdram` are the two resource types in the machine;
two files would be created: `allocations_cores.json` and
`allocations_sdram.json`.

#### `allocations_*.json`

Each allocation file contains a JSON object with two members: `type` and
`allocations`. The `type` member names the resource type allocated in the file.
The `allocations` member contains a JSON object which gives the *range* of
resources allocated to a particular vertex. For example,
a `allocations_cores.json` file may look like:

    {
        "type": "cores",
        "allocations": {
            "vertex0": [1, 2],
            "vertex1": [1, 2],
            "vertex2": [2, 3],
        }
    }

Note that the resource ranges are given as two-element arrays giving the start
(inclusive) and end (exclusive) of the range. In the above example, all of the
ranges indicate a single core has been allocated to each vertex.

### Routing Algorithms

Next, the above files are supplied to a routing algorithm which produces
another new file `routes.json`. The router must also be told which resource
type represents SpiNNaker *cores* since it needs to know which core sink
vertices are on to produce routes which end on those cores.

#### `routes.json`

*TODO*

### Routing Table Generation/Compression

The routing table generator may take any or all of the above files along with a
file `routing_keys.json` which enumerates the key and mask pairs associated
with each edge which must be included in SpiNNaker's multicast routing tables.
The output of this program is a file `routing_tables.json` which contains the
multicast routing tables for each SpiNNaker chip.

#### `routing_keys.json`

*TODO*

#### `routing_tables.json`

*TODO*

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
  represented by the vertex `mydevice`. A `location` and `route_endpoint`
  constraint are used in tandem:
  
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
  chip (1, 2). A `location` and `resource` constraint are used in tandem:
  
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


