# PyECS
A Python implementation of an Entity Component System

**Python >= 3.9 required**

****

## Architecture
Like every other ECS, this one has 3 main components + 2 "middleware" classes:

### Entities
Containers with a unique ID that hold all the references to the **Components** they own 
and also have a signature that is determined by performing a **bitwise OR** with every
component's signature.

### Components
Data structures owned by an **entity**.
Each component type is identified by a **signature**
(which is an integer with only one of it's bits set).

### Systems
Used to make **components** interact in order to actually give functionality to the simulation.

System update functions should be designed for parallelism.

### Signals
Used by systems to communicate events to other systems.
Signals are distributed to a system only if they are handled by the System.
Each signal can hold arbitrary data and systems must have custom handlers for each type of
signal it needs to handle, optionally subdivided by signature.

### Scenes
containers for **systems** and **entities** that also provides ways for them to 
create new entities, delete already existing entities & propagate **signals**.

A scene can be thought of as a level in a game.