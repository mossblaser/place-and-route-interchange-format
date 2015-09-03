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


File Format
-----------

A place/route problem and solution is broken down into various files.

TODO: Describe flow.

All files are encoded using [JSON](http://www.json.org/), a simple
human-readable, light-weight data-interchange format. High-performance JSON
libraries are available for all popular programming languages (and plenty of
unpopular ones too...). For each file, a [schema is provided](./schemas)
(written in [JSON Schema](http://json-schema.org/)) which defines the structure
of the data. You can automatically verify the structural correctness of a data
file against these schemas using [any of a number of
validators](http://json-schema.org/implementations.html) (we recommend
[jsonschema](https://github.com/Julian/jsonschema), a validator written Python
with a straight-forward command-line interface.
