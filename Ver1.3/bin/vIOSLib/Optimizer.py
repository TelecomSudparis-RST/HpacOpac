
""" 
vCDN Infrastructure Optimization Controller
=======================================

> Ignacio Tamayo, TSP, 2016
> Version 1.3
> Date: August 2016

This is the main controller of OMAC demo

..note:: When updating the items in the DB, do not set the date/time by localfunctions; Let the DB handle all timestamps using ONUPDATE and DEFAULT

All messages and logs are in Messages.py. This is to make it easy to change languages and to have unified messages

For  DB operations, mostly queries and listing, destroy the objects after use with del ARRAY[:] and end the Transaction with DBConn.endTransaction() 
For  DB modifications, update/add/deletes queries, end the Transaction with DBConn.endTransaction() before moving to another Query o listing

.. seealso:: DataModels.py Messages.py
	

:Example:

	connect( db_url ) # Connect to the DB
	
	createRandomInfrastructure()  #Create a random topology and build a model
	buildModel()
	
	updatePOPs()   # update the latest OpenStack data
	updateMetris()
	
	createRandomDemands()  # Create a Random set of Demands and optimize based on them
	consumeDemands()
	optimize()
	
	simulate()  # Simulate the impact on the Infrastructure of the selected changes
	
"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2016 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from random import random, seed			
#Used to randomize the Demands and the Infrastructure
from time import time								
#Used to calculate the time of decision making
import logging

from  DataModels import Hypervisor,Flavor,Instance, Metric, Demand, Demand
import Messages
import DBConnection 
import OpenStackConnection as OpenStack
import OptimizationModels
import SettingsFile

logger = logging.getLogger(__name__)

# Options read from the Config File somewhere else
# These options are read from the config file and are expected to be overriden

meterDurationHours = 6				
"""Default 6 hours to sample Metrics on the Telemetry"""
demandProbability = 0.5			
"""Default probability of a client v demand a vcdn f. Values in the range [0,1]"""
demandAmplitude = 100.0				
"""Maximum value for a Demand bw, in Mbps. Values > 0"""

INI_Section = "DEFAULT" 
""" This is the INI file section where we expect to find our values"""


DBConn = None
""" 
	Object holding the connection to the Database
	:type DBConn: DBConnection class
"""

OSMan = OpenStack.APIConnection()
""" Object holding the connection to the Nova API 
	:type OpenStack.APIConnection class
"""

Model = None
""" Object holding the connection to the HMAC Model for the calculations to take place
	:type OptimizationModels.HMAC class
"""

def readSettingsFile():
	"""
		This function asks the INI file parser module, that must have read the INI file, to look for the options in the sections and variables that are of interest for this module.
		
		If the options are not present in the INI file, the existing values are not modified
		
		This is so that we add or remove options from the INI file just by mofiying this functions. Also, the same INI entry can be read by many modules
		
		.. note:: Make sure that the SettingsFile module has been initialized and read a valid file
		
		::Example::
			SettingsFile.read(INI_file)
			Optimizer.readSettingsFile()
		
	"""
	global demandProbability
	global demandAmplitude
	global meterDurationHours
	global pollingWaitHours
		
	if SettingsFile.getOptionFloat(INI_Section,"demand_probability"):
		demandProbability = SettingsFile.getOptionFloat(INI_Section,"demand_probability")
	if SettingsFile.getOptionFloat(INI_Section,"demand_amplitude"):
		demandAmplitude = SettingsFile.getOptionFloat(INI_Section,"demand_amplitude")
	if SettingsFile.getOptionInt(INI_Section,"sample_period_hours"):
		meterDurationHours = SettingsFile.getOptionInt(INI_Section,"sample_period_hours")
	if SettingsFile.getOptionInt(INI_Section,"polling_frequency_hours"):
		pollingWaitHours = SettingsFile.getOptionInt(INI_Section,"polling_frequency_hours")
	#endif

def connect(url):
	""" 
	Connects to the provided DB String
	
		:param url is a sqlalchemy string, just like the ones in nova.conf [database]
		:type url String
		
		:returns: True if connection OK, False if not
	"""
	global DBConn	
	logger.debug(Messages.ConnectDB_S % url)
	DBConn = DBConnection.DBConnection(url)
	return DBConn.connect()
#enddef

def consumeDemands():
	"""
		Gets the Demands from the Database and, one by one; removes the Demanded BW from the Capacity Graph of the Model
		
		Invalid demands are ignored. Demands that request a pair (vCDN,POP) that does not exist are IGNORED. 
		
		A new model is created here, taking fresh information from the DB. This is because the Operator can be working on the Demands, alters or receives a change it the Topologie information (clientGroups, Locations, NetLinks, POPs, etc)
		and would like to re-run the Demands on top. So a new fresh Model is needed in this case to include the possible backend changes
		
		..seealso:: OptimizationModels.Model.consumeDemands()
		
		:returns:  True if all OK; False if there were some errors
				
	"""
	
	ret = True
	
	## Start from a Fresh model from the DB information
	if buildModel():
		try:
			DBConn.start()
			
			demandsList = DBConn.getDemands()
			
			logger.info(Messages.Consuming_Demands)
			
			if (demandsList):
				for d in demandsList[:]:
					
					# Check Valid demands, invalids are removed
					instance = getInstanceforDemand(d)
					if  instance == None:
						demandsList.remove(d)
						logger.error(Messages.Invalid_Demand_Client_S_vCDN_S_POP_S % (d.clientGroup.name, d.vcdn.name, d.pop.name ))
					
				#endfor
			
				return Model.consumeDemands(demandsList)
			
			#endif
		except:
			logger.exception(Messages.Exception_optimizing)
			return False
		finally:
			del demandsList[:]
			DBConn.cancelChanges()
			DBConn.end()
	else:
		logger.error(Messages.NoModel)
		return False
#enddef

def createRandomInfrastructure():
	""" 
		Updates values from the Infrastructure, non-OpenStack
	
		These values are parameters set by the Operator and its systems, in the production case.
		In this DEMO, this is a fake function to generate values and put them in the OMAC DB.
		
		Changes produced: ClientGroups.location and NetworkLinks table are shuffled ar random
		
		:returns:  True if all ok; False if there were some errors
		
		This is done by mapping the Model to a Random Tree graph
		
	"""
	
	#.. warning:: It has proven difficult to shuffle the POPs.location field, to move the POPs randomly. Even if we do a full shuffle and avoid repetitions, because of the constraint UNIQUE(POP.location); when the table is being updated it can happen that for an instant the location is duplicated. 
	#This triggers an error, the proper way would be to add a dummy location to start using is as a token for swapings locations.... or to remove the lock of Unique location.
	
	logger.info(Messages.Consuming_Demands)
	DBConn.start()
	LocationList = DBConn.getLocations()
	if (LocationList):
		try:
			# Make a random Graph with the locations in DB, and get the Links in the graph
			# The Location objects are linked to the Graph, do not delete them
			
			erg = OptimizationModels.Random(LocationList)
			
			
			linksList = erg.getLinkList()
			
			# Clear all the Network links, and take them from the ER Graph
			for nl in DBConn.getNetworkLinks():
				DBConn.drop(nl)
			DBConn.applyChanges()
			
			for nl in linksList:
				DBConn.add(nl)
			DBConn.applyChanges()

			logger.info(Messages.Updated_NetworkLinks)
			
			# Assign the ClientGroup locations at will, only on the access layer
			borderLocations = erg.getAccessLocations()
			clients = DBConn.getClientGroups()
			for c in clients:
				index = int(random() * len(borderLocations))
				c.locationId = borderLocations[ index].id
			#endfor
			DBConn.applyChanges()
			
			logger.info(Messages.Updated_ClientLocations)
			return True
		except:
			logger.exception( Messages.Exception_updating_Infrastructure)
			DBConn.cancelChanges()
			return False
	else:
		logger.error( Messages.No_Locations)
		return False
	DBConn.end()
	
#enddef


def createRandomDemands():
	""" 
		Updates values from the Demand registers, non-OpenStack.
		These values are parameters set by the Operator and its systems.
		
		In this DEMO, this is a fake function to generate values and put them in the OMAC DB.
		
		A demand, in OMAC paper; is said to be d[v][f], but as only 1 server is to supply this demand, and q vCDN can be in more than 1 server, this leads to associate a demand to an Instance, which is 1 server that holds a vCDN inside
		
		The Demands are created via a random number and a threshold
		For all Clients and all Instances: There is a demand if a random probability is bigger than 'demandProbability' value.
		If so, the bw of the demand is set in the range of values [0 ; demandAmplitude] aproximately.
		
		:returns:  True if all ok; False if there were some errors.
		
	"""
	
	logger.info(Messages.Create_Random_Demands)
	
	try:
		
		DBConn.start()
		
		# Get all instances of all Instances. Get all clientGroups
		InstaceList = DBConn.getInstanceList()
		ClientGroupList = DBConn.getClientGroups()
		
		if InstaceList  and ClientGroupList  :
			
			logger.debug(Messages.CreatingRandomDemands_D_probaF_amplitudeD % (len(InstaceList) *len(ClientGroupList),demandProbability,demandAmplitude))
			
			# Remove all Demands.
			demands = DBConn.getDemands()
			if demands:
				for d in demands:
					DBConn.drop(d)
				DBConn.applyChanges()
				
				logger.info(Messages.Deleted_Demands)
			
			# Make random associations
			accum = 0
			for i in InstaceList:
				seed()
				for clientGroup in ClientGroupList:
					rnd = random()
					if rnd < demandProbability:
						d = Demand(clientGroupId = clientGroup.id, 
									popId = i.popId,vcdnId=i.vcdnId, 
									volume =  (demandProbability - rnd) * 2 * 100, 
									bw =  (demandProbability - rnd) * 2 * demandAmplitude 
									)  
						
						
						# (demandProbability - rnd) gives a number  in the interval [0,demandProbability]; demandProbability < 1
						# (demandProbability - rnd) * 2 * demandAmplitude gives a number in the desired range
						DBConn.add(d)
						accum = accum+1
			
			# Update DB
			DBConn.applyChanges()
				
			logger.info(Messages.Created_D_Demands % accum )
		
		else:
			logger.error( Messages.NoInstances)
			return False
		#endif
		
		DBConn.end()
		return True
		
	except:
		logger.exception( Messages.Exception_updating_Demand)
		DBConn.end()
		return False
#enddef



def simulate( migrationList = [],redirectList = [], instantiationList = []):
	"""
		This functions simulates that the Migrations/Redirections/Instantiations were actually executed; changed the Data in the Systems and would be reflected as changes in the Model
		
		This procedure starts from a new Model, having fresh Topologie information from the DB.
		
		Then the requested changes are simulated, altering the list of Instances in the Model, and also altering the list of Demands. 
		This is because the simulation suposes that the CDN system performs all the needed changes so that the Demands will point to where the vCDN were Migrated or Instantiated or Redirected.
		So the Model now works on a simulated list of Instances and updated Demands
		
		Then the Model is asked to check the representation of the number of Instances, from the new list of simulated instances
		
		The simulated Demands are checked against the simulated list of Instances; as the moving of Instances could have caused some Demands to now become invalid
		
		Finally, the Model is asked to consume the simulated list of Demands to have an updated Gomory-Hu Tree of remaining capacity. Hopefully, a better scenario that the original
		
		All simulated objects and elements are deleted, the DB is not altered in any way
		
		
		:param migrationsList: List of Migrations to execute
		:type migrationsList: HmacResult[]
		:param redirectsList: List of Redirects to execute
		:type redirectsList: Redirect[]
		:param invalidDemandList: List of Demands to instantiate
		:type invalidDemandList: Demands[]
		
		:returns:  True if all OK; False if there were some errors
		
		..note:: This function updates/Changes the Model's Gomory-Hu Tree.
				
	"""
	
	global DBConn
	global Model
	
	logger.info(Messages.Simulating_Migrations) 
	
	try:
		
		# Build model, first
		buildModel()
		
		DBConn.start()
		realInstances = DBConn.getInstanceList()
		realDemands = DBConn.getDemands()
		fakeInstances = []
		fakeDemands = []
		
		for i in realInstances:
			fakeInstances.append( OptimizationModels.FakeInstance( popName = i.pop.name, 
														popId = i.popId, 
														vcdnName = i.vcdn.name , 
														vcdnId = i.vcdnId ,
														popLocationName = i.pop.location.name)
								)
		for d in realDemands:
			fakeDemands.append(	OptimizationModels.FakeDemand(clientGroupLocationName = d.clientGroup.location.name, 
													clientGroupName = d.clientGroup.name,
													popLocationName = d.pop.location.name,
													popName = d.pop.name, 
													popId = d.popId, 
													vcdnName = d.vcdn.name , 
													vcdnId = d.vcdnId,
													bw=d.bw)
								)
		
		#Delete all the Objects not to affect the DB, as this is a simulations and the DB should not change
		
		del realInstances[:]
		del realDemands[:]
		DBConn.cancelChanges()
		DBConn.end()
		
		
		# Place new fake instances where needed, from Migrations and Instantiations
		# Get the Demands and adjust the targets to go to the Redirected/Migrated/Instantiated
		
		logger.info(Messages.Adjusting_Instances_Demands) 
		
		for m in migrationList:
			
			logger.debug(Messages.Simulate_Migration_vCDN_S_from_POP_S_to_POP_S % (m.instance.vcdn.name, m.instance.pop.name, m.dstPOP.name))
			
			found = False
			for f in fakeInstances:
				if m.instance.vcdnId  == f.vcdnId and m.instance.popId == f.popId:
					found = True
					break
			
			if found:
				fakeInstances.remove(f)
				logger.debug(Messages.Deleted_Fake_Instace_POP_S_vCDN_S % (m.instance.pop.name, m.instance.vcdn.name))
				newInstance = OptimizationModels.FakeInstance(  popName = m.dstPOP.name, 
													popId = m.dstPopId , 
													popLocationName = m.dstPOP.location.name,
													vcdnName = m.instance.vcdn.name , 
													vcdnId = m.instance.vcdnId
													
												)
			
				if newInstance not in fakeInstances:
					fakeInstances.append(newInstance)
					logger.debug(Messages.Added_Fake_Instace_POP_S_vCDN_S % (m.dstPOP.name, m.instance.vcdn.name))
				else:
					del newInstance
				
			for f in fakeDemands:
				if f.vcdnId == m.instance.vcdnId and f.popId == m.instance.popId:
					
					logger.debug(Messages.Update_Fake_Demand_fromPOP_S_toPOP_S % (f.popName, m.dstPOP.name) )
					
					f.popId  = m.dstPopId
					f.popName = m.dstPOP.name
					f.popLocationName = m.dstPOP.location.name
					
		
		for r in redirectList:
			logger.debug(Messages.Simulate_Redirection_vCDN_S_from_POP_S_to_POP_S % (r.instance.vcdn.name, r.instance.pop.name, r.dstPOP.name))
			for f in fakeDemands:
				if f.vcdnId == r.instance.vcdnId and f.popId == r.instance.popId and f.clientGroupName == r.demand.clientGroup.name and f.clientGroupLocationName == r.demand.clientGroup.location.name :
					
					logger.debug(Messages.Update_Fake_Demand_fromPOP_S_toPOP_S % (f.popName, r.dstPOP.name) )
					
					f.popId  = r.dstPopId
					f.popName = r.dstPOP.name
					f.popLocationName = r.dstPOP.location.name
			
		for i in instantiationList:
			
			logger.debug(Messages.Simulate_Instantiation_vCDN_S_on_POP_S % (i.vcdn.name, i.pop.name))
			
			newInstance = OptimizationModels.FakeInstance(vcdnId = i.vcdnId , 
										popId = i.popId, 
										vcdnName = i.vcdn.name, 
										popName = i.pop.name ,
										popLocationName = i.pop.location.name)
			
			if newInstance not in fakeInstances:
				fakeInstances.append(newInstance)
				logger.debug(Messages.Added_Fake_Instace_POP_S_vCDN_S % (newInstance.popName, newInstance.vcdnName))
			else:
				del newInstance
			
		
		logger.info(Messages.Adjusting_Model) 
		
		#Adjust the POPs Sizes according to the new list of Instances after all the chagnes
		Model.updateFakeInstances(fakeInstances)
		
		# Check Valid demands compared to the Instances after all the changes, invalids are removed
		for d in fakeDemands[:]:
			match = False
			for f in fakeInstances:
				if  d.vcdnId == f.vcdnId and d.popId == f.popId:
					match=True
					break
			#endfor
			if not match:
				fakeDemands.remove(d)
				logger.debug(Messages.Invalid_Demand_Client_S_vCDN_S_POP_S % (d.clientGroupLocationName, d.vcdnName, d.popName))
		
		logger.info(Messages.Running_Demands)
		
		# Do consume the adjusted Demands
		Model.consumeFakeDemands(fakeDemands)
		
	
		del fakeInstances[:]
		del fakeDemands[:]
		
		
	except:
		logger.exception(Messages.Exception_Simulating)
		return False
	
	# Done, the Gomory-Hu Tree and the Capacity can be drawn
	return True
	
	#enddef
	

def getInstanceforDemand(d):
	"""
		For a given Demand d, requesting a vCDN from a POP, this function checks if effectively there is any Instance of the vCDN in that POP
		
		:param d: demand to check for a valid Instance
		:type d: Demand
		
		:returns:   the Instance object or None if not found
		:rtype: Instance or None

	"""
	return DBConn.getInstanceOf(vcdnId = d.vcdnId, popId = d.popId )
#enddef

def getInstance(pop,vcdn):
	"""
		For a given POP and a vCDN, this function retuns the Instance of them both, if it exists
		
		:param pop: POP to check for a valid Instance
		:type pop: POP
		:param vcdn: vCDN to check for a valid Instance
		:type vcdn: vCDN
		
		:returns:   the Instance object or None if not found
		:rtype: Instance or None

	"""
	return DBConn.getInstanceOf(vcdnId = vcdn.id, popId = pop.id )
#enddef

#enddef

def updatePOPs():
	""" Reads values of the OpenStack APIs for the POPs
	
		With the login provided in the POP ( the provided user must have "admin" access)
			It updates the Hypervisors table, adding if new hypervisors are found. The total POP capacity values are the sum of all its hypervisors
			It updates the Flavors table, only with the Public Flavors (as Tenants should use these flavors). Only rootDisk information is captured
		
		With the login provided for each vCDN, a user with "_member_" access to the Tenant:
			It updates the limits found for the Tenant in the POPs
			It updates the number of instances for the Tenant in the POPs
						
		:returns:  True is all the POPs were updated; False if any of the POPs failed
			
	"""
	global DBConn
	global OSMan
	
	_errors = False
	
	logger.info(Messages.Updating_OpenStack)
	
	DBConn.start()
	
	popList = DBConn.getPOPList()
	if (popList):
		for pop in popList:
			OSMan.disconnect()
			
			OSMan.setURL(pop.url,pop.region)
			
			OSMan.setCredentials(pop.tenant,pop.loginUser,pop.loginPass)
			if not OSMan.connect():
				logger.error(Messages.NoConnect_Pop_S % pop.name)
				_errors = True
				continue
				#Not connect, log error and continue to NEXT POP
			
			#These are the accumulated values through the Hypervisors in the POP. The POP has resources equal to the sum of its Hypervisors
			found = False
			hyperDB = None
			accumCurCPU =0
			accumCurRAM =0
			accumCurDisk=0
			accumInstances =0
			accumMaxCPU =0
			accumMaxRAM =0
			accumMaxDisk =0
			
			
			
			try:
				for hyper in OSMan.getHypervisors():
					# First we see if there is alreay a Hypervisor entry for this POP in the DB. If there is not, we will create this new Hypervisor
					for hyperDB in pop.hypervisors:		
						if (hyperDB.name == hyper.hypervisor_hostname):		
							found=True
							break
					#endfor
					if not found:
						hyperDB = Hypervisor(hyper.hypervisor_hostname, pop.id)
						logger.debug(Messages.Created_Hypervisor_S_POP_S % (hyperDB.name,pop.name))
						DBConn.add(hyperDB)
						
					
					DBConn.applyChanges()
					
					#Update existing values	and increasing the counter for POP resources

					hyperDB.model = hyper.hypervisor_type
					accumCurCPU += hyper.vcpus_used
					accumCurRAM += hyper.memory_mb_used
					accumCurDisk += hyper.local_gb_used
					accumInstances += hyper.running_vms
					accumMaxCPU += hyper.vcpus
					accumMaxRAM += hyper.memory_mb
					accumMaxDisk += hyper.local_gb
					
					hyperDB.updateMaxValues (cpu = hyper.vcpus, ram = hyper.memory_mb, disk = hyper.local_gb)
					hyperDB.updateCurValues (cpu = hyper.vcpus_used, ram = hyper.memory_mb_used, disk = hyper.local_gb_used, instances= hyper.running_vms)
					
					logger.debug(Messages.Updated_Hypervisor_S_POP_S % ( hyperDB.name , pop.name))
					
					#As we have updated the Hypervisor in hyperDB, we must make this change permanent, by flushing the Session, before getting the next Hypervisor
					DBConn.applyChanges()
					
				#endfor
			
			except:
				logger.exception(Messages.Exception_Update_Hypervisor_S_POP_S % ( hyperDB.name , pop.name))
				_errors = True
				
			found=False
			flavorDB = None
			try:
				for flav in OSMan.getPublicFlavors():
					# First we see if there is alreay a Flavor entry for this POP in the DB. If there is not, we will create this new Flavor
					for flavorDB in pop.flavors:		
						if (flavorDB.osId == flav.id):		
							found=True
							break
					#endfor
					if not found:
						flavorDB = Flavor(flav.name, flav.id, pop.id)
						#flavorDB.created_at = datetime.
						logger.debug(Messages.Created_Flavor_S_POP_S % (flav.name,pop.name))
						DBConn.add(flavorDB)
					
					
					#Update existing values	 
					flavorDB.updateValues (name = flav.name,cpu = flav.vcpus, ram = flav.ram, disk = flav.disk, isPublic = True)
					logger.debug(Messages.Updated_Flavor_S_POP_S % ( flav.name , pop.name))
					
				#endfor
				DBConn.applyChanges()
			except:
				_errors = True
				logger.exception(Messages.Exception_Update_Flavor_S_POP_S % ( flav.name , pop.name))
				
				
			#Update existing values	 
			pop.updateMaxValues (cpu = accumMaxCPU, ram = accumMaxRAM, disk = accumMaxDisk , netBW = pop.totalNetBW)
			pop.updateCurValues (cpu = accumCurCPU, ram = accumCurRAM, disk = accumCurDisk, instances = accumInstances, netBW = 0)
		
			DBConn.applyChanges()
			# End of operations with AdminLogin
			
			logger.info(Messages.Updated_Pop_S % pop.name)
			
			### Starting operations with Tenant Login ###
			found=False
			InstanceDB = None
			
			vCDNList = DBConn.getvCDNs()
			
			
			if (vCDNList):
				for vcdn in vCDNList:
					try:
						OSMan.disconnect()
						OSMan.setCredentials(vcdn.tenant,vcdn.loginUser,vcdn.loginPass)
						if not OSMan.connect() or OSMan.getLimits()==None:
							logger.error(Messages.NoConnect_Pop_S % pop.name)
							_errors = True
							continue
							### Next tenant tries to login
						
						
						lim = OSMan.getLimits()
						
						found=False
						for InstanceDB in vcdn.instances:
							if (InstanceDB.popId == pop.id):
								found=True
								logger.debug(Messages.Found_Instance_S_at_POP_S_LimitsInstances_D % ( vcdn.name ,InstanceDB.pop.name,lim.curInstances))
								break
						#endfor
						
						
						
						if found and lim.curInstances ==0:		
							# There is an instance in the DB but not in the OpenStack, so it is deleted
							DBConn.drop(InstanceDB.metric)
							DBConn.drop(InstanceDB)
							logger.debug( Messages.Deleted_Instance_S_at_POP_S % (vcdn.name , pop.name))
							continue  
							 ### Next tenant tries to login
						elif not found and lim.curInstances > 0: 		
							# There no not an instance in the DB but it is in the OpenStack, so it is added
							InstanceDB = Instance(vcdn.id, pop.id)
							DBConn.add(InstanceDB)
							InstanceDB.updateMaxValues (cpu = lim.maxCPU, ram = lim.maxRAM, instances = lim.maxInstances)
							InstanceDB.updateCurValues (cpu = lim.curCPU, ram = lim.curRAM, instances = lim.curInstances)
							
							logger.debug(Messages.Added_Instance_S_at_POP_S % (vcdn.name, pop.name))
						elif found and lim.curInstances > 0:
							#Update existing values
							InstanceDB.updateMaxValues (cpu = lim.maxCPU, ram = lim.maxRAM, instances = lim.maxInstances)
							InstanceDB.updateCurValues (cpu = lim.curCPU, ram = lim.curRAM, instances = lim.curInstances)
							
							logger.debug( Messages.Updated_Instance_S_at_POP_S % (vcdn.name, pop.name))
						
						DBConn.applyChanges()	
						
					except:
						_errors = True
						logger.exception(Messages.Exception_Update_vCDN_S_POP_S % ( vcdn.name , pop.name))
						DBConn.cancelChanges()
						continue
				#endfor
			#endif 
				
			# End of operations with Tenant Login
			logger.info(Messages.Updated_Tenants_Pop_S % pop.name)
			
		#endfor
		DBConn.applyChanges()
	#endif
	DBConn.end()
	return not _errors
#enddef



def updateMetrics():
	""" Reads values of the OpenStack Telemetry APIs for all the Instances
		With the login provided for each vCDN, a user with "member" access to the Tenant and read access to Telemetry
		
		Better if executed after updatePOPs() to have up-to-date Instance information
			
		Starts looking for all Instances in a POP. 
			For this instance, the vCDN credentials are used to access the Telemetry of the vCDN
			The Metrics are updated for this Instance. If there is no Metrics, the next Instance in the loop is taken
			If the vCDN credentials do not login to the Telemetry, the next Instance is the look is taken
		
		Finished once checked all the POPs
		
		:returns:  True is all the POPs were updated; False if any of the POPs failed
		
	"""
	global DBConn
	global OSMan
	global meterDurationHours			
	#Parameter read from config file
	
	_errors = False 
	
	logger.info(Messages.Updating_OpenStack_Metrics)
	
	DBConn.start()
	
	popList = DBConn.getPOPList()
	
	if (popList):
		for pop in popList:
			
			PopCurNetBW = 0	
			## Summing all the curNetBW of all the instances in the POP gives the current BW used in the POP
			
			instanceList = pop.instances
			if (instanceList is not None) and (instanceList ):
				for i in instanceList:
					# Starting operations with to check the metrics of this instance
					OSMan.disconnect()
					OSMan.setURL(pop.url,pop.region)
					OSMan.setCredentials(i.vcdn.tenant,i.vcdn.loginUser,i.vcdn.loginPass)
					if not OSMan.connectMetrics():
						logger.error(Messages.NoConnect_Pop_S % pop.name)
						_errors = True
						continue
						### Next Instace tries to login
					
					logger.debug( Messages.Getting_Metric_Pop_D_tenant_S % (pop.name,i.vcdn.name))
					
					meter = OSMan.getMetrics(meterDurationHours)
						
					#try:
					metricDB = None
					metricDB = i.metric
					if metricDB == None or metricDB==[]:  
						#There are no metrics created for this instance, lets make one
						metricDB = Metric(i.id)
						DBConn.add(metricDB)
						logger.debug( Messages.Added_Metric_Instance_D % i.id)
					#except:
						#logger.error(Messages.ERROR_Update_DB_Metric )
						#continue  #Next Instance
				
					#either way; new or old; update
					metricDB.update(meterDurationHours, meter.sampletime, meter.todict() )
					PopCurNetBW = PopCurNetBW + meter.values["network.outgoing.bytes.rate"]._avg + meter.values["network.incoming.bytes.rate"]._avg
					logger.debug( Messages.Updated_Metric_Instance_D % i.id)
				#endfor
				# End of operations with Tenant Login
				
				
				logger.info( Messages.Updated_Metrics_Pop_S % pop.name )
				logger.info(Messages.Updated__D_OpenStack_Metrics % len(instanceList))
			#endif
			pop.curNetBW = PopCurNetBW / 1024	
			# Because meter.values["network.outgoing.bytes.rate"]._avg is on kbps and pop.curNetBW has to be in Mbps
			
			pop.maxNetBW = pop.totalNetBW	
			#Copy the manual-set value totalNetBW
			
			DBConn.applyChanges()  
			### This updates all the values found for a POP, puts all in the DB
			# if DBConn.endTransaction() is not done here; the Foreign keys POP - Instance - Metric might give errors. Please leave this call here
			

		#endfor
		
	#endif
	
	DBConn.applyChanges()		### This updates all the values left for update
	DBConn.end()
	return _errors
	
#enddef

Optimization_ERROR = -1

def optimize():
	""" 
		Gathers information from the DB and calls optimization with the information.
		
		This optimization is a Heurisitic approach, based on the Demands.
		
		The Global Model is built from fresh information from the DB, this is to include any backend changes made to the Topology or Demands.
		
		This stores the result in the DB
		
		:returns:s the amount of seconds it took to calculate this, or Optimization_ERROR if error
		:rtype: float > 0.0 or Optimization_ERROR
		
		.. seealso:: OptimizationModels.Model.optimizeHMAC()
		
	"""
	global Model
	global DBConn
	
	logger.info(Messages.Optimizating)
	
	# This creates a new Model from the DB and passes the Demands to have a remaining capacity Graph
	if consumeDemands():
		
		#Delete the previous HmacResults Entries
		DBConn.start()
		migList = DBConn.getHmacResults()
		if (migList):
			for m in migList:
				DBConn.drop(m)
			DBConn.applyChanges()
			logger.info(Messages.Deleted_Migrations)
		DBConn.end()
		#endif
				
		try:
			
			DBConn.start()
			demands = DBConn.getDemands()
			vcdns =  DBConn.getvCDNs()
			migCostKList =  DBConn.getMigrationCostMultiplierList()
			
			migrationList = None
			invalidDemands = None
			
			if (demands):
				
				t0 = 0.0+time()
				
				migrationList  = Model.optimizeHMAC(demands)
				
				logger.info(Messages.HMAC_optimized)
					
				#If as a result, there are HmacResults to make, they are written to the DB
				#This is done to Isolate the Modeling only from where and how is the result stored
				
				###If as a result, there are Invalid Demands, then the Demands Table is updated to register this interesting result
				DBConn.applyChanges()
				
				if (migrationList is not None and migrationList ):  
					for m in migrationList:
						DBConn.add(m)
					DBConn.applyChanges()
					
				migrationList = DBConn.getMigrationsSorted()
				if (migrationList is not None and migrationList ):  
					for m in migrationList:
						migCostMultiplier = DBConn.getMigrationCostMultiplier(m.instance.popId, m.dstPopId)
						if migCostMultiplier != None:
							m.cost = m.cost * migCostMultiplier
							logger.debug(Messages.Updated_MigrationCost_MigrationId_D% (m.demandId) )
					
					DBConn.applyChanges()
				
				
				
				if (migrationList is not None and migrationList ) :  
					for m in migrationList:
						migCostMultiplier = DBConn.getMigrationCostMultiplier(m.instance.popId, m.dstPopId)
						if migCostMultiplier != None:
							m.cost = m.cost * migCostMultiplier
							logger.debug(Messages.Updated_MigrationCost_MigrationId_D% (m.demandId) )
						DBConn.add(m)
				
				
				
				# Add the missing information for the OMAC model
				Model.omac.setvCDNs(vcdns)
				Model.omac.setMigrationCost(migCostKList)
				Model.omac.setDemands(demands)
				
				# Write the .DAT file for OMAC Optimization
				if not Model.omac.optimize():
					logger.error(Messages.No_OMAC_Optimize)
				else:
					logger.info(Messages.OMAC_optimized)
					
				t1 = 0.0+time()
				
				DBConn.applyChanges()
				
				
				logger.info(Messages.Optimized_F % (t1-t0))
				
				return (t1-t0)
				
			else:
				logger.error(Messages.NoDemands)
				
			DBConn.end()
		except:
			logger.exception(Messages.Exception_optimizing)
			
	else:
		logger.error(Messages.NoModel)
		
	
	return Optimization_ERROR
#enddef


def buildModel():
	""" 
		Gathers information from the DB and calls creates an HMAC/OMAC Model
		..note:: Call this before optimize()
		
		This resets/rebuils the global object Model
		
		:returns:  True if Model was built; False if not.
		
	"""
	
	global DBConn
	global Model
	
	logger.info(Messages.Building_Model) 
	DBConn.start()
	try:
		
		#Build nodes with locations and links
		locations = DBConn.getLocations()
		netLinks = DBConn.getNetworkLinks()
		if (locations and netLinks ):
			Model = OptimizationModels.Model(locations,netLinks)
		else:
			logger.error(Messages.Missing_Elements_to_Build_Model)
			return False  # No model, just quit
		del locations[:] 
		del netLinks[:] 
		DBConn.cancelChanges()
	except:
		logger.exception(Messages.Exception_Building_Model)
		return False
		# No model, just quit. The Global Model remains unchanged

	try:
		#Place POPs in infrastructure
		pops = DBConn.getPOPList()
		if (pops):
			Model.setPOPs(pops)
		else:
			logger.error(Messages.NoPOPs)
			# If there were  no POPs; at least the Graphs can be built yet, so we continue
		### DO not call del pops[:]  as these objects are now linked to the Modele's Graphs
		DBConn.cancelChanges()
	except:
		logger.exception(Messages.Exception_Model_POPS)
		return False
	try:
		#Place ClientGroups in infrastructure
		clientGroups = DBConn.getClientGroups()
		if (clientGroups):
			Model.setClientGroups(clientGroups)
		else:
			logger.error(Messages.NoClients)
			# If there were  no ClientGroups; at least the Graphs can be built yet, so we continue
		del clientGroups[:]
		DBConn.cancelChanges()
	except:
		logger.exception(Messages.Exception_Model_Clients)
		return False
	
	Model.buildGomoryTree()
	DBConn.end()
	
	return True
#enddef

