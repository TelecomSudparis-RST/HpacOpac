Use Cases
=========

> Ignacio Tamayo, TSP, 2016
> Version 1.3
> Date: August 2016

## Use Case 1:

The Operator for testing purposes, can randomize some parameters of the infrastructure:

 * NetworkLinks between the Locations
 * Locations of the ClientGroups to serve, being placed in the border of the Operator Network
 * Demands to serve, from a clientGroup to a vCDN in a specific POP, with a certain volume and BW.

## Use Case 2:

The Operator sets or updates the basic infrastructure parameters:

 * Locations of the infrastructure
 * NetworkLinks between the Locations
 * POPs of the infrastructure, their Location, OpenStack credentials, capacity values, etc
 * vCDNs of the infrastruture, their VM size, OpenStack credentials, the default BW to offer the clients, etc
 * ClientGroups to serve, and their Location
 * Migration cost values from one POP to another
 * Demands to serve, from a clientGroup to a vCDN in a specific POP

## Use Case 3:

 * The Operator checks the current placement of the vCDNs and its parameters:

> These values are taken directly from OpenStack Controllers (one by each POP) and might differ from information registered in other systems.

## Use Case 4:

The Operator executes the HPAC optimization of the infrastructure based on its current Topology, its capacities, the OpenStack POPs state and the demands (could be an aggregated of current demands or a forecast of demands). 

The results are stored in the DB, not executed. This is because the actual changes in the CDN system might involve other systems and integrations.

The operator must provide significant and relevant data about the demand and the infrastructure. The current state is taken directly from OpenStack Controllers.

## Use Case 5:

The Operator selects some of the optimizations and simulates its impact on the infrastructure. The selected changes might affect the simulated topology and the simulated demands.

The results are not stored in the DB, they are calculated and showed once only.

The operator be aware that any selected optimization might affect the existing demands, perhaps making them invalid or requiring them to be altered along with the optimization.
