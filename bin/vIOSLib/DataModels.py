""" 

Modules for the Data Model, DB Tables, on sqlalchemy
====================================================

> Ignacio Tamayo, TSP, 2016
> Version 1.4
> Date: Sept 2016

.. seealso:: db/vIOS_db.sql

.. note:: When updating the items in the DB, do not set the date/time by local functions. Let the DB handle all timestamps using ONUPDATE and DEFAULT

.. warning:: The functions __unicode__() is needed for Flask-Admin, representing by a text the single instance of the object.

.. note:: Because of SQLAlchemy, the `modified_at` value is actually set when the last MODIFICATION took place, not the last time it was queried for information.

Units and Values
----------------

 * All Integers; except Metrics values and the MigrationCostMultiplier that are Floats

|   Disk                                     | Unit |
| ------------------------------------------ | ---- |
| POP.totalDisk, .maxDisk, .curDisk          |  GB  |
| Hypervisor.maxDisk, .curDisk               |  GB  |
| Flavor.rootDisk (*)                        |  GB  | 
| Metric.diskrootsize_x                      |  GB  |  
| vCDN.vDisk                                 |  GB  |

(*) .ephemeralDisk, .swapDisk not used

|         RAM                                | Unit |
| ------------------------------------------ | ---- |
| POP.totalRAM, .maxRAM, .curRAM             |  MB  |
| Hypervisor.maxRAM, .curRAM                 |  MB  |
| Flavor.RAM                                 |  MB  |
| Metric.memory_x                            |  MB  |
| vCDN.vRAM                                  |  MB  |
| Instance.maxRAM, .curRAM                   |  MB  |

|             virtual CPU                    |  Unit  |
| ------------------------------------------ | ------ |
| POP.totalCPU, .maxCPU, .curCPU             |  unit  |
| Hypervisor.maxCPU, .curCPU                 |  unit  |
| Flavor.CPU                                 |  unit  |
| Metric.vcpus_x                             |  unit  |
| vCDN.vCPU                                  |  unit  |
| Instance.maxCPU, .curCPU                   |  unit  |

|           Instances  = VMs                 |  Unit  |
| ------------------------------------------ | ------ |
| POP.curInstances                           |  unit  |
| Hypervisor.curInstances                    |  unit  |
| Metric.instance_x                          |  unit  |
| Instance.curInstances, .maxInstances       |  unit  |

|           BW                               | Unit |
| ------------------------------------------ | ---- |
| vCDN.defaultQosBW                          | kbps |
| Demand.bs                                  | Mbps |
| Metric.networkXBps                         | kbps |
| POP.totalNetBW, .maxNetBW, .curNetBW (*)   | Mbps |
| NetworkLink.capacity                       | Mbps |
| clientGroup.connectionBW                   | Mbps |
| HmacResult.minBW                           | Mbps |

(*) Calculated value as the SUM of the Virtual Machies of the Tenant in the POP (via its Metrics. Check updateMetrics() )

(*) Hypervisor.maxNetBW, Hypervisor.curNetBW  are not used

.. note:: MigrationCostMultiplier.costMultiplier is a float value, with no units. This float is multiplied to the internal HmacResult cost calculated by OMAC, so the Operator can weight their migration decision.

The HmacResult.cost is calculated as vCDN.vDisk * HmacResult path hops in the Topologie Graph, in [GB] units.

> ..note:: In order to use the CASCADE from the DB instead of the CASCADE SQLAlchemy, the relationship is declared in the TARGET table using casacade="all".
>
> SQLAlchemy links the tables in inverse order; from the one-to-many side. [Reference](http://docs.sqlalchemy.org/en/latest/orm/collections.html#passive-deletes)
> We use 'passive_deletes=True' in the PARENT Class, in the relation attribute.
> Otherwise, it will load the object and set the FK to NULL, which would break the DB Consistency.
> All the relationships declared ON CASCADE in the DB have "passive_deletes=True" attribute set.

"""


"""
..license::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from sqlalchemy import Table,  Column, Integer, String, ForeignKey, DateTime, Boolean, func, Float
from sqlalchemy.orm import mapper, relationship, backref
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

from urlparse import urlparse
### Used to build the HTTP URL for the POPs

Base = declarative_base()

# Description of the tables for mapping. Only Columns and keys are defined here.
# Constrains are detailed in vIOS_db.sql (in the SQL DB) so that any other tool using the DB respects the limits and brakes nothing
# .. seealso:: vIOS_db.sql 


class Location(Base):
	"""
		This indicates a node in the Operators Infrastructure Topology.
		A Location connects to the ClientGroups and can have a POP or a ClientGroup.
		
		UNIQUE (name): To avoid confusion on the related tables. A location name is unique in a certain area.
		
		..seealso:: ClientGroup.location, POP.location
		
		Attributes:
			geo (String): Optional String that could be used to indicate the physical position of the Location
			clientGroups (ClientGroup[]): One or more clientGroups connected to this Location. Inverse attribute is `ClientGroup.location`.
			pop (POP): One (only one) POP located in the Location. Inverse attribute is `POP.location`.
			created_at (DateTime):
			modified_at (DateTime):
		
	"""
	__tablename__ = 'Locations'
	id = Column(Integer, primary_key=True)
	name = Column(String)
	geo = Column( String)
	clientGroups = relationship("ClientGroup", backref = backref('location'),passive_deletes=True)
	#Using strings as the Classes are not compiled until the end, so if Objects there will be a compilation error
	pop = relationship("POP", backref = backref('location',uselist = False), uselist = False, passive_deletes=True)
	####One-to-one Relation
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())
	
	def __init__(self, name="Here"):
		"""
			:param name: Unique name of the location
			:type name: String
		"""
		self.name = name
	#enddef
	    
	def __unicode__(self):
		"""
			:returns: Location.name
			:rtype: String
		"""
		return self.name

#endclass

class NetworkLink(Base):
	"""
		A Link between any 2 Locations
		
		UNIQUE (locationAId,locationBId) as not to have 2 entries for the same link. 
		At DB it is CHECKED that (locationAId <> locationBId) to avoid loops.
		Birectionality is not checked in DB, so (locationAId,locationBId) and (locationBId,locationAId) can happen.
		
		Attributes:
			locationAId (int): A valid ID of the Location.
			locationBId (int): A valid ID of the Location.
			capacity (int): Capacity of the link, in Mbps
			locationA (Location): One Location end of the link.
			locationB (Location): Other Location end of the link.
			created_at (DateTime): 
			modified_at (DateTime):
		
	"""
	__tablename__ = 'NetLinks'
	id = Column(Integer, primary_key=True)
	locationAId= Column( Integer, ForeignKey('Locations.id'))
	locationBId=Column( Integer, ForeignKey('Locations.id'))
	capacity = Column( Integer)
	capacityUnits = "Mbps"
	locationA = relationship("Location",foreign_keys="NetworkLink.locationAId"  )
	locationB= relationship("Location",foreign_keys="NetworkLink.locationBId" )
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())

	def __init__(self, locationAId, locationBId, capacity=0):
		"""
			:param locationA: Location Id source
			:type locationA: int
			:param locationB: Location Id destination
			:type locationB: int
			:param capacity: Capacity of the link in Mbps (Mega bits-per-second)
			:type capacity: int
			
			(locationA,locationB) is UNIQUE
			(locationB,locationA) = (locationA,locationB) bidirectional
	
		"""
		self.locationAId = locationAId
		self.locationBId = locationBId
		self.capacity = capacity
		
	#enddef
	
	def toString(self):
		""" 
		:returns: LocationA  <-[X Mbps]-> LocationB 
		:rtype: String
		
		"""
		return self.locationA.name + " <-["+str(self.capacity)+" "+ self.capacityUnits +"]-> " + self.locationB.name
    #enddef
    
#endclass

class MigrationCostMultiplier(Base):
	"""
		This value is multiplied to the calculated cost to tune the Migration cost between 2 POPs.
		The Cost Multiplier is considered birirectional, as the NetworkLinks.
		
		UNIQUE (popAId,popBId) as not to have 2 entries for the same migration. 
		At DB it is CHECKED that (popAId <> popBId) to avoid loops.
		Birectionality is not checked in DB, so (popAId,popBId) and (popBId,popAId) can happen.
		
		Attributes:
			popA (POP): One POP end of the Migration
			popB (POP): Other POP end of the Migration
			costMultiplier (float): Value that could be used as cost multiplier. This is a float value, defaults to 1.0
		
	"""
	__tablename__ = 'MigrationCostMultipliers'
	id = Column(Integer, primary_key=True)
	popAId = Column( Integer, ForeignKey('POPs.id'))
	popBId = Column( Integer, ForeignKey('POPs.id'))
	popA = relationship("POP",foreign_keys="MigrationCostMultiplier.popAId" )    
	popB = relationship("POP",foreign_keys="MigrationCostMultiplier.popBId")
	costMultiplier = Column(Float, default=1.0)

	def __init__(self, popAId, popBId, cost=1.0):
		"""
			:param popA: POP source Id
			:type popA: int 
			:param popB: POP destination Id
			:type popB: int 
			:param cost: Value > 0 that indicates the cost. This is a value given by the provider
			:type cost: float
			
			(popA,popB) is UNIQUE
			(popB,popA) = (popA,popB) bidirectional
	
		"""
		self.popAId = popAId
		self.popBId = popBId
		self.costMultiplier = cost
	#enddef

    
	def toString(self):
		""" 
		:returns: PopA  --[CostX]--> popB 
		:rtype: String
		"""
		return self.popA.name + " --["+str(self.costMultiplier)+"]--> " + self.popB.name
	#enddef
#endclass


class ClientGroup(Base):
	"""
	A Set of Clients that request the vCDN service.
	
	UNIQUE (name) as the Clients can be placed in any location, the name must be unique to be able to identify them.
	
	.. seealso:: Demand.clientGroup, QOSMap.clientGroup
	
	Attributes:
		locationId (int): Location ID where the ClientGroup is connected 
		demands (Demand[]): Demands made by this clientGroup. Inverse attribute is `Demand.clientGroup`.
		connectionBW (int): Access network connection BW for this clientGroup. This is not used in any calculation, it is an informational value. Value is int > 0.
		created_at (DateTime): 
		modified_at (DateTime):
	
	"""
	__tablename__ = 'ClientGroups'
	id = Column(Integer, primary_key=True)
	
	locationId = Column( Integer, ForeignKey('Locations.id'))
	demands = relationship("Demand", backref = backref('clientGroup'),passive_deletes=True)
	name = Column(String)
	connectionBW = Column(Integer)
	connectionBWUnits = "Mbps"
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())
	
	def __init__(self, name, locationId,connectionBW=0):
		"""
			:param name: Name of the client group. Is not unique
			:type name: String
			:param location: A valid location Id, from a Locations
			:type location: int
			
			(name,location) is UNIQUE
			
		"""
		self.name = name
		self.locationId = locationId
		self.connectionBW = connectionBW
	#enddef

	def __unicode__(self):
		"""
			:returns: clientGroup.name
			:rtype: String
		"""
		return self.name + "@" + self.location.name
	#enddef
	
#endclass   


class POP(Base):
	"""
	This is an OpenStack DC, located in a Location node, and capable of hosting a vCDN instance. 
	It is identified by its OpenStack KeyStone endpoint and the appropriate credentials
		
	UNIQUE = (region,url,region,tenant,loginUser) as not to have 2 entries for the OpenStack controller. If the Same OpenStack server is used, either there must be a different user/tenant/region
	UNIQUE = (name) as to have single identifiable names
	UNIQUE = (locationId) as to keep a single POP in each location. This assumtion might change, but it will impact most of the OMAC/HMAC implementation code (and break the foreing key)
	
	Attributes:
	
		`url` to be the Public Keystone Endpoint, versioned
		`region` can be NULL
		`url` is expected to be the Public/Admin Keystone
		`totalDisk`,`totalRAM`,`totalCPU`, `totalNetBW` are parameters set by the Optimizer, based on their installation and knowledge of the Infra
		`maxDisk`,`maxRAM`,`maxCPU` are parameters calculated by OpenStack, by summing the capacities of the Hypervisors member of this POP
		`curDisk`,`curRAM`,`curCPU`,,`curInstances` are parameters calculated by OpenStack, by summing the usage of the Hypervisors member of this POP
		`curNetBW` is calculated by OpenStack, by summing the network statistics of all the Instances in the POP
		
		hypervisors (Hypervisor[]): Compute Nodes of this POP. Inverse attribute is `Hypervisor.pop`.
		flavors (Flavor[]): Flavors found on this POP to instantiate VMs. Inverse attribute is `Flavor.pop`.
		instances (Instance[]): vCDNs instantiated in this POP. Inverse attribute is `Instance.pop`.
		migrations (HmacResult[]): HmacResults that point to this POP as destination of a migration. Inverse attribute is `HmacResult.dstPop`.
		demands (Demand[]): Demands that are requested from this POP. Inverse attribute is `Demand.pop`.
		redirects (AlteredDemand[]): Redirects that point to this POP as optimal destination. Inverse attribute is `Redirect.dstPop`.
		name (String): Name to identify this POP.
	
	Units:
	
		`xDisk` in GB
		`xRAM` in MB
		`xCPU` in units
		`xNetBW` in Mbps
	
	"""
	__tablename__ = 'POPs'
	id = Column(Integer, primary_key=True)
	locationId = Column( Integer, ForeignKey('Locations.id'))
	#location
	hypervisors = relationship("Hypervisor", backref = backref('pop'),passive_deletes=True)
	flavors = relationship("Flavor", backref = backref('pop'),passive_deletes=True)
	instances = relationship("Instance", backref = backref('pop'),passive_deletes=True)
	migrations = relationship("HmacResult", backref = 'dstPop',passive_deletes=True)
	demands = relationship("Demand", backref = backref('pop'),passive_deletes=True)
	redirects = relationship("AlteredDemand", 		backref = 'dstPop',passive_deletes=True)
	name = Column( String)
	url = Column( String)
	region = Column( String)
	tenant = Column( String)
	loginUser = Column( String)
	loginPass = Column( String)
	maxDisk = Column( Integer)
	maxRAM = Column( Integer)
	maxCPU = Column( Integer)
	maxNetBW = Column( Integer)
	totalDisk = Column( Integer)
	totalRAM = Column( Integer)
	totalCPU = Column( Integer)
	totalNetBW = Column( Integer)
	curDisk = Column( Integer)
	curRAM = Column( Integer)
	curCPU = Column( Integer)
	curNetBW = Column( Integer)
	curInstances   = Column( Integer)
	
	netBWUnits = "Mbps"
	RAMUnits = "MB"
	diskUnits = "GB"
	
	
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())
	
	def __init__(self, name, locationId, url, tenant,loginUser,loginPass ,region=None ):
		"""
			:param name: Name of the POP, set by operator
			:type name: String
			:param location: LocationId from the Locations table
			:type location: int
			:param tenant: Admin Tenant name, not tenant Id
			:type tenant: String
			:param loginUser: Admin user, user with Admin rights
			:type loginUser: String
			:param loginPass:
			:type loginPass: String
			:param region:
			:type region: String
			
			:returns: A POP
			:rtype: POP
		"""
		self.name = name
		self.locationId = locationId
		self.region = region
		self.url = url
		self.tenant = tenant
		self.loginUser = loginUser
		self.loginPass = loginPass
	#enddef
	
	def updateMaxValues(self, cpu, ram, disk,netBW):
		"""
			:param cpu: count of vCPUs available
			:param ram: MB of RAM available
			:param disk: GB of disk available
			
			This corresponds to the sum of all the hypervisors capacity in the POP:
			
				> nova hypervisor-list
				> nova hypervisor-show
		"""
		self.maxCPU = cpu
		self.maxRAM = ram
		self.maxDisk = disk
		self.maxNetBW = netBW
	#enddef
	
	def updateCurValues(self, cpu, ram, disk,instances,netBW):
		"""
			:param cpu: count of vCPUs used
			:param ram: MB of RAM used
			:param disk: GB of disk used
			:param instances: # of instances used
			
			This corresponds to the sum of all the hypervisors in the POP
			
		"""
		self.curCPU = cpu
		self.curRAM = ram
		self.curDisk = disk
		self.curInstances = instances
		self.curNetBW = netBW
	#enddef 
	 
	def setTotalValues(self, cpu, ram, disk,instances,netBW):
		"""
			:param cpu: count of vCPUs in total in the POP
			:type cpu: int
			:param ram: MB of RAM  in total in the POP
			:type ram: int
			:param disk: GB of disk  in total in the POP
			:type disk: int
			:param instances: # of instances supported in total in the POP
			:type instances: int
			:param netBW: Mbps of total network BW capacity in total in the POP
			:type netBW: int
						
			This corresponds to the installed infrastructure, these parameters are set by the operator
			
		"""
		self.totalCPU = cpu
		self.totalRAM = ram
		self.totalDisk = disk
		self.totalInstances = instances
		self.totalNetBW = netBW
	#enddef  
	
	def canHostVCDN(self, AvCDN):
		"""
		Used by OptimizationModels.HMAC.optimize()
		
		Returns True if the vCDN fits in the POPs; cheking vDisk, vRAM et vCPUs.
		
		The POP's available resources are calculated as (.TotalX - .curX)
		
		The vCDN's size is taken from the attribues vDisk vRAM vCPU and vNetBW
		
		Comparison is "greater than" only. On "==" condition, it is considered that it does not fit
		
		:param AvCDN: A vCDN to test if it fits in the POP resources.
		:type AvCDN: vCDN object
		
		:returns:s True if the vCDN fits in the POPs, cheking vDisk, vRAM, vCPU and vNetBW
		
		"""
		
		try:
			ret = 	( 
				((self.totalDisk - self.curDisk) > AvCDN.vDisk)
				)
				
				### In our Test Infrastructure, the OpenStack Compute Nodes are already to the limit, so the full condition is removed
				
				#((self.totalDisk - self.curDisk) > AvCDN.vDisk) and \
				#((self.totalRAM - self.curRAM) > AvCDN.vRAM ) and \
				#((self.totalCPU - self.curCPU) > AvCDN.vCPU) and \
				#((self.totalNetBW - self.curNetBW) > AvCDN.vNetBW)
				
		except TypeError:
			
			#self.curDisk is a value obtained from OpenStack. If at any rate this value is NULL 
			#	(because of problems getting OpenStack info), then we assume full capacity and return True
			
			ret = True
		return ret
	#enddef
	
	def canHostVCDN_String(self, AvCDN):
		"""
		Used for logging the hosting condition
		
		..seealso:: canHostVCDN()
		
		:param AvCDN: a vCDN to be instantiated in a POP
		:type AvCDN: vCDN object
		
		:returns: a String with the compared values
		:rtype: String
		
		"""
		ret = 	"RAM: POP %d vCDN %d; Disk: POP %d vCDN %d; CPU: POP %d vCDN %d; NetBW: POP %d vCDN %d;" % (  (self.totalDisk - self.curDisk) , 
																												AvCDN.vDisk,
																												(self.totalRAM - self.curRAM) ,
																												AvCDN.vRAM,
																												(self.totalCPU - self.curCPU) ,
																												AvCDN.vCPU,
																												(self.totalNetBW - self.curNetBW) ,
																												AvCDN.vNetBW 
																											)
		
		return ret
	#enddef
	
	def __unicode__(self):
		"""
			:returns: POP.name
			:rtype: String
		"""
		return self.name
	#enddef
	
	def dashboardUrl(self):
		"""
		From the Keystone URL, the Horizon Dashboard URL is built
		This can be used to offer a HTML link to the Dashboard
		
		:param url: The Keystone Auth URL for the OpenStack Data Center
		:type url: String
		
	"""
		url = "http://127.0.0.1/horizon"
		x = urlparse(self.url)
		url = "%s://%s/horizon" % (x.scheme , x.netloc.split(":")[0] )
		return url
	
#endclass 


class Hypervisor(Base):
	"""
		A compute node from an OpenStack DC
		
		UNIQUE = (name,popId). 
		2 Hypervisors can belong to a single POP, as long as they have different names. 
		2 Hypervisors can have the same name, but on different POPs. This reflects OpenStack characteristics
		
		maxX are values that the OpenStack Nova finds as available in the HW
		curX are values that the OpenStack Nova is currently using from the HW
		
		.. note:: `maxNetBW` and `curNetBW` are not used
		
		.. seealso:: OpenStack Nova Python API
		
		
	"""
	__tablename__ = 'Hypervisors'
	id = Column(Integer, primary_key=True)
	popId = Column( Integer, ForeignKey('POPs.id') )
	
	name = Column( String)
	maxDisk = Column( Integer)
	maxRAM = Column( Integer)
	maxCPU = Column( Integer)
	maxNetBW = Column( Integer)
	curDisk = Column( Integer)
	curRAM = Column( Integer)
	curCPU = Column( Integer)
	curNetBW = Column( Integer)
	curInstances = Column( Integer)
	
	RAMUnits = "MB"
	diskUnits = "GB"
	
	model = Column( String)
	""" OpenStack Model value, as String"""
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())

	def __init__(self, name, popId):
		"""
			:param name: name of the Hypervisor, is not unique
			:type name: String
			:param popId: Id of the POP where this hypervisor is.
			:type popId: int
			
			Touple (name,popId) is UNIQUE
			
		"""
		self.popId = popId
		self.name = name
	#enddef
     
	
    
	def updateMaxValues(self, cpu, ram, disk):
		"""
			:param cpu: count of vCPUs available
			:param ram: MB of RAM available
			:param disk: GB of Storage available
			:type cpu,ram,disk: int
		"""
		self.maxCPU = cpu
		self.maxRAM = ram
		self.maxDisk = disk
	#enddef
    
	def updateCurValues(self, cpu, ram, disk,instances):
		"""
			:param cpu: count of vCPUs in use
			:param ram: MB of RAM in use
			:param disk: GB of Storage in use
			:type cpu,ram,disk: int
		"""
		self.curCPU = cpu
		self.curRAM = ram
		self.curDisk = disk
		self.curInstances = instances
	#enddef
	def __unicode__(self):
		return self.name
	#enddef
#endclass


class Flavor(Base):
	"""
		Flavor available in the OpenStack DC. This is not used for any operation, but is left for future extension as this could be used together with the available Images to determine what VMs can be launched.
		
		UNIQUE = (osId,popId). 2 POP can have the same Flavor ID in OpenStack, coincidence. 1 POP has unique Flavors. This reflects OpenStack characteristics.
		
		.. seealso:: OpenStack Nova Python API
		
		Attributes:
			osId (String): ID String value used by OpenStack to identify the flavor.
			rootDisk (int): USED for capacity calculation
			
	"""
	__tablename__ = 'Flavors'
	id = Column(Integer, primary_key=True)
	popId = Column( Integer, ForeignKey('POPs.id') )
	name = Column( String)
	osId = Column( String)
	RAM = Column( Integer)
	CPU = Column( Integer)
	rootDisk = Column( Integer)
	ephemeralDisk = Column( Integer)
	""" Not used for any calculation"""
	swapDisk = Column( Integer)
	""" Not used for any calculation"""
	isPublic = Column( Boolean)
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())
	
	RAMUnits = "MB"
	diskUnits = "GB"
	
	def __init__(self, name, osId, popId):
		"""
			:param name: Name used to identify the Flavor
			:type name: String
			:param osId: OpenStack Id of the Flavor, as name can change by the OpenStack ID remains
			:type osId: String
			:param popId: POP where these flavors are seen
			:type popId: int
			
			Touple (osId,popId) is UNIQUE
		"""
		self.name = name
		self.popId = popId
		self.osId = osId
	#enddef
     
    
	def updateValues(self, name, cpu, ram, disk,isPublic):
		"""
			:param name: name given in OpenStack to the flavor
			:type name: String
			:param cpu: CPU needed for this flavor
			:param ram: MB of ram needed for this flavor
			:param disk: GB of disk needed for this flavor
			:type cpu, ram, disk : int
			:param isPublic: True | False
			:type isPublic: boolean
			
		"""
		self.name = name
		self.CPU = cpu
		self.RAM = ram
		self.rootDisk = disk
		self.isPublic = isPublic
	#enddef
	
	def __unicode__(self):
		return self.name
	#enddef
#endclass  


class vCDN(Base):
	"""
	A vCDN is identified by a single OpenStack Tenant. This Tenant would login in all the OpenStack POPs of the Infrastructure where resources can be allocated for it.
	
	UNIQUE = (name). Because each vCDN is identified by a single name.

	`url`,`loginUser`,`loginPass`,`tenant`  are the same credentials used by the Nova CLI client, usually put in Envinroment Variables.
	
	The capacity values (RAM, disk, CPU, netBW) are values that are compared to the available resources of a POP to determine if the vCDN can be instantiated or not.
	.. seealso:: POP.canHostVCDN()
	
	Attributes:
		vInstances (int): Amount of VMs needed in a POP for this vCDN. A vCDN instance can be made of several VMs.
		defaultQosBW (int): It is the BW in kbps to be given ClientGroups connecting to this vCDN, by default. BW in kbps. NOT used for any calculation, informational value.
		dnsDomain (String): Designate DNS Domain for this vCDN. It MUST end with (.). If this value is not NULL, the vCDN Credentials will be used to connect to Desigate and operate this Tenant's DNS Domain.
		instances (Instance[]): Instances that is vCDN has in some POPs. Inverse attribute is `Instance.vcdn`.
		demands (Demand[]): Demands that request this vCDN. Inverse attribute is `Demand.vcdn`.
	
	"""
	
	__tablename__ = 'vCDNs'
	id = Column(Integer, primary_key=True)
	name = Column( String)
	tenant = Column( String)
	loginUser = Column( String)
	loginPass = Column( String)
	vInstances = Column( Integer)
	vDisk = Column( Integer)
	vRAM = Column( Integer)
	vCPU = Column( Integer)
	vNetBW = Column( Integer)    
	defaultQosBW = Column( Integer, default=0 ) 
	netBWUnits = "Mbps"
	qosBWUnits = "kbps"
	RAMUnits = "MB"
	diskUnits = "GB"
	dnsDomain = Column( String)
	instances = relationship("Instance", backref = backref('vcdn'),passive_deletes=True)
	demands = relationship("Demand", backref = backref('vcdn'),passive_deletes=True)
	
	def __init__(self, name,tenant,loginUser,loginPass):
		"""
			:param name: Name to identify this vCDN Client
			:type name: String
			:param tenant: Tenant name, not tenant Id
			:type tenant: String
			:param loginUser:
			:type loginUser: String
			:param loginPass:
			:type loginPass: String
		"""
		self.name = name
		self.tenant = tenant
		self.loginUser = loginUser
		self.loginPass = loginPass
	#enddef
	
	
	def __unicode__(self):
		"""
		:returns: vCDN name
		"""
		return self.name
	#enddef
#endclass



class Instance(Base):
	"""
		An instance is a set of VMs and resources allocated in a POP for a vCDN. From here the clientGroups are served
		
		UNIQUE = (popId,vcdnId). 1 server that holds several vCDNs inside, and a vCDN can be in many POPs, but the pair is unique.
		
		Attributes:
			metric (Metric): The one and only Metric object holding the OpenStack Telemetry values for this Instance. Inverse attribute is `Metric.instance`.
			migrations (HmacResult[]): HmacResults that intend to migrate this Instance. Inverse attribute is `HmacResult.instance`.
		
	"""
	__tablename__ = 'Instances'
	id = Column(Integer, primary_key=True)
	popId = Column( Integer, ForeignKey('POPs.id') )
	vcdnId = Column( Integer, ForeignKey('vCDNs.id') )
	metric = relationship("Metric",  uselist = False , backref = backref('instance', uselist = False),passive_deletes=True)	
	## One to One relationship
	migrations = relationship("HmacResult", backref = 'instance',passive_deletes=True)
	maxRAM = Column( Integer)
	maxCPU = Column( Integer)
	curRAM = Column( Integer)
	curCPU = Column( Integer)
	maxInstances = Column( Integer)
	curInstances = Column( Integer)
	
	RAMUnits = "MB"
	
	created_at = Column( DateTime, default=func.now() )
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())
	
	def __init__(self, vcdnId, popId):
		"""
		:param vcdnId: Id of the vCDN.
		:param popId: Id of the POP where this vCDN exists.
		
		This refers if the tenant of vcdnId has at least 1 VM in popId
		
		Touple (vcdnId,popId) is UNIQUE
		"""
		self.popId = popId
		self.vcdnId = vcdnId
	#enddef
     
	
    
	def updateMaxValues(self, cpu, ram, instances):
		"""
			:param cpu: count of vCPUs available
			:param ram: MB of RAM available
			:param instances: # of instances available
			:type cpu,ram,instances: int
			
			This corresponds to the Quota limit of the tenant of the vcdnId in this popId
				> nova quota-defaults
			
			.. note:: There is no Disk in the Quota values
			
		"""
		self.maxCPU = cpu
		self.maxRAM = ram
		self.maxInstances = instances
	#enddef
    
	def updateCurValues(self, cpu, ram, instances):
		"""
			:param cpu: count of vCPUs used
			:param ram: MB of RAM used
			:param instances: # of instances used
			:type cpu,ram,instances: int
			
			This corresponds to the Quota limit of the tenant of the vcdnId in this popId
			> nova quota-show
			
			.. note:: There is no Disk in the Quota values
		"""
		self.curCPU = cpu
		self.curRAM = ram
		self.curInstances = instances
	#enddef
	def __unicode__(self):
		"""
		
		:returns: vCDN@Pop
		:rtype: String
		
		"""
		return self.vcdn.name + "@" + self.pop.name
	#enddef
	
	
#endclass 

class Metric(Base):
	"""
	These are the OpenStack Telemetry aggregated values for each Instance.
	
	The Metrics are the {min, max, avg} statistics of a set of Meters from the OpenStack Telemetry, aggregated by Tenant and linked to an Instance object.
	
	.. seealso:: OpenStack Telemetry Python API
	
	Attributes:
		instanceId (int): The only Instance for which these Metrics are gathered.
		durationHours (int): The amount of hours to gather samples and perform the aggregation and statistics.
		sampletime (String): Timestamp of the minimal This is in STRING as not to mix the timestamps of the DB with the Ceilometer DB
		modified_at (DateTime): 
	
	"""
	__tablename__ = 'Metrics'
	id = Column(Integer, primary_key=True) 
	instanceId = Column( Integer, ForeignKey('Instances.id'))
	durationHours = Column( Integer, default=1 )    
	cpuUtil_min = Column( Float)
	cpuUtil_max = Column( Float)
	cpuUtil_avg = Column( Float)
	diskrootsize_min = Column( Float)
	diskrootsize_max = Column( Float)
	diskrootsize_avg = Column( Float)
	instance_min = Column( Float)
	instance_max = Column( Float)
	instance_avg = Column( Float)
	memory_min = Column( Float)
	memory_max = Column( Float)
	memory_avg = Column( Float)
	networkInBytes = Column( Float)
	networkOutBytes = Column( Float)
	networkInBps_min = Column( Float)
	networkInBps_max = Column( Float)
	networkInBps_avg = Column( Float)
	networkOutBps_min = Column( Float)
	networkOutBps_max = Column( Float)
	networkOutBps_avg = Column( Float)
	vcpu_min = Column( Float)
	vcpu_max = Column( Float)
	vcpu_avg = Column( Float)
	
	networkBytesUnits = "kB"
	networkBpsUnits = "kbps"
	cpuUtilUnits = "%"
	diskrootsizeUnits = "GB"
	memoryUnits = "MB"
	
	sampletime = Column( String)  
	
	modified_at = Column( DateTime, onupdate=func.now(), default=func.now())

	def __init__(self, instanceId):
		"""
			:param instanceId: instance (vCDN in POP) that is being measured
			:type instanceId: int > 0
		"""
		self.instanceId = instanceId
	#enddef

	def update(self, duration, sampletime, karg):
		"""
			:param duration: Hours that this metric contains. It is assumed to be measured now(), taking the last samples for a duration X hours
			:type duration: int
			:param sampletime: TimeStamp in String, when the sample was taken.
			:type sampletime: String
			:param karg: Dictionary of values of the metric. ceilometer meter-list
			:type karg: Dictionary
			
			This corresponds to mapping the OpenStack objects
			
			.. seealso:: OpenStack.py
			
			.. todo:: networkInBytes/networkOutBytes to be discussed, as the value grouped by tenant/resource changes
			
		"""
		self.durationHours = duration #In hours
		self.sampletime = sampletime #String
		self.networkInBytes = karg["networkInBytes"]
		self.networkOutBytes = karg["networkOutBytes"]
		self.networkInBps_min = karg["networkInBps_min"]
		self.networkInBps_max = karg["networkInBps_max"]
		self.networkInBps_avg = karg["networkInBps_avg"]
		self.networkOutBps_min = karg["networkOutBps_min"]
		self.networkOutBps_max = karg["networkOutBps_max"]
		self.networkOutBps_avg = karg["networkOutBps_avg"]
		self.cpuUtil_min = karg["cpuUtil_min"]
		self.cpuUtil_max = karg["cpuUtil_max"]
		self.cpuUtil_avg = karg["cpuUtil_avg"]
		self.diskrootsize_min = karg["diskrootsize_min"]
		self.diskrootsize_max = karg["diskrootsize_max"]
		self.diskrootsize_avg = karg["diskrootsize_avg"]
		self.instance_min = karg["instance_min"]
		self.instance_max = karg["instance_max"]
		self.instance_avg = karg["instance_avg"]
		self.memory_min = karg["memory_min"]
		self.memory_max = karg["memory_max"]
		self.memory_avg = karg["memory_avg"]
		self.vcpu_min = karg["vcpu_min"]
		self.vcpu_max = karg["vcpu_max"]
		self.vcpu_avg = karg["vcpu_avg"]
		
		#self.networkBytesUnits= karg["networkBytesUnits"]
		#self.networkBpsUnits= karg["networkBpsUnits"]
		#self.cpuUtilUnits= karg["cpuUtilUnits"]
		#self.diskrootsizeUnits= karg["diskrootsizeUnits"]
		#self.instanceUnits= karg["instanceUnits"]
		#self.memoryUnits= karg["memoryUnits"]
		#self.vcpuUnits  = karg["vcpuUnits"]

		
	#enddef
	
	def __unicode__(self):
		"""
		:returns: instance Id value
		:rtype: String
		"""
		return str(self.instanceId)
	#enddef
	
#endclass




class Demand(Base):
	"""
	
	A Demand comes from a clientGroup (which is attached to a Location), asking for a vCDN from a POP (CDN DNS or Anycast mechanisms could be in place, this reflects how the clients are directed to the appropriate CDN servers).
	
	A Demand might actually ask for an non-existing pair (vCDN,POP) (This pair is an Instance), then turning this Demand in an InvalidDemand.
	This should ideally associate a Demand to an Instance, but not necessarily as the Instance can just have disappeared when the Demand was calculated or measured.
	
	These values are external to vIOSimulator because they must be gathered by the CDN services.
	
	UNIQUE = (ClientGroupId,popId,vcdnId). As only 1 optimal server is to supply the demand for a vCDN,
	
	Attributes:
		clientGroup (ClientGroup):
		pop (POP):
		vcdn (vCDN):
		migration (HmacResult): Migration related for this Demand.  Inverse attribute `HmacResult.demands`.
		redirect (AlteredDemand):  Redirection triggered for this Demand.  One and only one. Inverse attribute `AlteredDemand.demand`.
		invalidInstance (boolean): True if the demanded pair (vCDN,POP) is actually an exiting Instance.
		volume (int): A number presenting the demand volume, concurrent demands, demand's importance, etc. This value is only used for sorting.
		bw (float): Total BW required for this Demand, in Mbps.
		created_at (DateTime):
	"""
	__tablename__ = 'Demands'
	
	id = Column(Integer, primary_key=True)
	clientGroupId = Column(  Integer, ForeignKey('ClientGroups.id'))
	# clientGroup in ClientGroup.demands
	popId = Column(  Integer , ForeignKey('POPs.id'))
	# pop in POP.demands
	vcdnId = Column(  Integer , ForeignKey('vCDNs.id'))
	# vcdn in vCDN.demands
	hmacResultId = Column(  Integer , ForeignKey('HmacResults.id')) 
	# migration in HmacResult.demands
	
	redirect = relationship("AlteredDemand", 
					cascade="all, delete-orphan",
                    backref = backref('demand', uselist = False)) #### One-to-one relationship
	invalidInstance = Column (Boolean, default = False)
	volume = Column( Integer , default=0)
	bw = Column (Float, default = 0)
	bwUnits = "Mbps"
	created_at = Column( DateTime, default=func.now() )
	
	def __init__(self, clientGroupId, popId,vcdnId,volume=0, bw=0.0):
		"""
			:param clientGroupId: Id of the ClientGroup demanding videos
			:type clientGroupId: int
			:param popId: Id of the POP related to this Demand
			:type popId: int
			:param vcdnId: Id of the vCDN being requested in this Demand
			:type vcdnId: int
			:param volume: An informational value, used for sorting the Demands
			:type volume: int
			:param bw: BW taken by this demand, in [Mbps]
			:type bw: float
			
			The set (clientGroupId,popId, vcdnId) is UNIQUE
			
		"""
		self.clientGroupId = clientGroupId
		self.popId = popId
		self.vcdnId = vcdnId
		self.volume = volume
		self.bw = bw
		
	#enddef
	
	def __unicode__(self):
		"""
			:returns: Demand Id
			:rtype: String
		"""
		return str(self.id)
	#enddef


class AlteredDemand(Base):
	"""
		An Altered Demand is a Demand that has to be re-directed to another POP as to optimize it
		
		Attributes:
			demand (Demand):
			dstPop (POP):
			created_at (DateTime):
		
	"""
	__tablename__ = 'AlteredDemands'
	
	id = Column(Integer, primary_key=True)
	demandId = Column(  Integer, ForeignKey('Demands.id'))
	dstPopId = Column(  Integer , ForeignKey('POPs.id'))
	# demand on Demand.redirect
	# dstPop on Pop.redirects
	
	created_at = Column( DateTime, default=func.now() )
		
	def __init__(self, demandId=1, dstPopId=1):
		"""
			:param demandId: Id of the original Demand
			:type demandId: int
			:param popId: Id of the POP where to alter this Demand to
			:type popId: int
			
			Set (demandId) is UNIQUE
			
		"""
		self.demandId = demandId
		self.dstPopId = dstPopId
		
	#enddef
	
	def __unicode__(self):
		"""
			:returns: Demand Id
			:rtype: String
		"""
		return self.demand.id
	#enddef
#endclass

class HmacResult(Base):
	"""
		This class and table in DB is for the migrations triggered by HMAC algorithm in OptimzationModesl.HMAC.optimize()
		
		.. seealso:: Optimizer.py
		
		unique (instanceId,dstPopId)
		
		Attributes:
			cost (float): Value that is produced by HMAC, calculated as the vCDN.size * migration path hops.
			delay (float): Value that is produced by HMAC, calculated as the vCDN.size / minimum link capacity.
			minBW (float): The minimum link BW found on the Gomory Tree for this migration. Used to know the limit BW for the migration. In Mbps.
			demands (Demand[]): Demands that are optimized by this migration. Inverse attribute is `Demand.migration`.
		"""
	
	__tablename__ = 'HmacResults'
	
	id = Column(Integer, primary_key=True)
	dstPopId = Column( Integer, ForeignKey('POPs.id'))
	# dstPop in POP.migrations
	instanceId = Column( Integer, ForeignKey('Instances.id'))
	# instance in Instance.migrations
	cost = Column(Float)
	delay = Column(Float)
	delayUnits = "mins"
	minBW = Column(Float)
	minBWUnits = "Mbps"
	created_at = Column( DateTime, onupdate=func.now(), default=func.now())
	demands = relationship("Demand", backref = backref('migration'),passive_deletes=True)

	demandsIds = []
	### Used to store the Demand.id while optimizing.
	
	def __init__(self,  dstPopId, instanceId, delay = 0, cost = 0, minBW = 0):
		"""
			
			:param dstPopId: id of the POP destination of the migration.
			:param instanceId: id of the Instance to be migrated.
			:type  dstPopId, instanceId: int, being the foreing keys of the table.
			
			:param delay: Delay calculated for this migration; in seconds.
			:type delay: int
			:param cost: A relative cost for the Migration. This value could be multiplied by a MigrationCostMultiplier, if it exists.
			:type: int
			:param minBW: Minimum BW found on the migration path, in Mbps.
			:type minBW: int
			:param migrate: True if this is a real Migration, False if this is a Redirection.
			:type migrate: boolean
			
			.. warning:: (instance.popId != dstPopId)
	
		"""
		
		self.dstPopId = dstPopId
		self.instanceId = instanceId
		self.delay = delay
		self.cost = cost
		self.minBW = minBW
		self.demandsIds = []
	#enddef

	
	
	def __unicode__(self):
		"""
		:returns: Result ID
		:rtype: String
		"""
		return str(self.id)
	#enddef
	
#endclass


