""" 

Messages dictionary
==================

This module takes care of logging, using levels ERROR|DEBUG. Other levels could be added in the future

This is to make it easier to translate the language of this tool and to centralize the logging behavior

> Ignacio Tamayo, TSP, 2016
> Version 1.3
> Date: August 2016

"""


"""
..licence::

	vIOS (vCDN Infrastructure Optimization Simulator)

	Copyright (c) 2019 Telecom SudParis - RST Department

	Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""


AdminPageTitle = 'vIOSimulator - DB Management'
Errors_updating_POPs = "There were some errors while updating the POPs"
Errors_updating_Metrics = "There were some errors while updating the Metrics from the POPs"
Error_building_Topologie = "There were some errors while building the Topologie graph"
Errors_random_links = "There were some errors while creating random Links"
ERROR_creating_Demands = "ERROR creating random demands"
ERROR_consuming_Demands = "ERROR calculating capacity consumed by demands"
Exception_drawing_Topologie = "Exception ocurred while drawing the Topologie"
ERROR_creating_Demands = "ERROR creating random demands"
ERROR_optimizing = "ERROR while optimizing"

Updated_Topo = "Topologie updated with random links"
Created_Demands = "Demands generated randomly"
Updated_POPs = "Information updated from OpenStack Controllers"
Optimized_F = "Optimal migrations calculated in %f seconds"

Missing_Elements_to_Build_Model =  "Missing elements to build an OMAC/HMAC Model (Locations and Network Links)"


NoPOPs = "There are no POPs found in the DB"
NovCDNs = "There are no vCDNs found in the DB"
POP_not_found = "POP not found in DB"
vCDN_not_found = "vCDN not found in DB"
NoDemands = "There are no demands registered in the DB"
NoNetworkLinks = "There are no Network Links registered in the DB"


###
### Optimizer.py
###

Create_Random_Topologie = "Creating a Random Topologie"
Consuming_Demands = "Consuming Demands BW on topologie capacity"

Random_Graph_Created = "A Random Topologie Graph has been created"
Updated_NetworkLinks = "The Network Links have been replaced by the random topologie"
Updated_ClientLocations = "The Client Groups have been distributed in the new topologie"

Exception_updating_Infrastructure =  "Exception ocurred while updating the Infrastructure Topologie"
Exception_updating_Demand = "Exception ocurred while creating random Demands"
Exception_optimizing = "Exception ocurred while executing the Optimization"

CreatingRandomDemands_D_probaF_amplitudeD = "Creating random %d Demands, p=%f, amplitude=%d "
Created_D_Demands = "Created %d random demands "
Updated__D_OpenStack_Metrics = "Updated OpenStack Metrics for %d instances"

Invalid_Demand_Client_S_vCDN_S_POP_S = "Invalid demand from ClientGroup '%s' for vCDN '%s' at POP '%s' "

No_OMAC_Optimize = "Unable to perform OMAC optimization"
Deleted_Demands = "Demands deleted from the DB"
Deleted_Migrations = "Migrations deleted from the DB"
Updated_Demands_QosBW = "Updated the demanded QoSBW based on vCDN information"
HMAC_optimized = "Finished running HMAC"
OMAC_optimized = "Created OMAC CPLEX data file"
Optimized_F = "Optimization executed in %f seconds"

Exception_Building_Model =  "Exception ocurred while building the OMAC/HMAC Model"

Updated_MigrationCost_MigrationId_D = "Migration cost updated for Migration %d"

Create_Random_Demands = "Creating Random Demands"

Updating_OpenStack = "Updating the OpenStack POP information"
Updating_OpenStack_Metrics = "Updating the OpenStack Metrics information for all Tenants"
Connected_POP_S = "Connected to POP '%s'"
Optimizating = "Running the Optimization algorithm"

Exception_Model_POPS = "Exception ocurred while placing the POPs in the OMAC/HMAC Model"
NoClients =  "There are no ClientGroups found in the DB"
Exception_Model_Clients = "Exception ocurred while placing the Clients in the OMAC/HMAC Model"

Exception_updating_Topologie =  "Exception ocurred while updating the Topologie"


Exception_Metrics_Tenant_S_POP_S = "Unable to get Metrics for Tenant %s in POP %s "

Created_Hypervisor_S_POP_S = " Created hypervisor '%s' for POP '%s' "

Created_Flavor_S_POP_S = " Created flavor '%s' for POP '%s' "
Updated_Hypervisor_S_POP_S = " Updated hypervisor %s for POP %s"

Updated_Flavor_S_POP_S = " Updated flavor %s for Pop %s"

Exception_Update_Hypervisor_S_POP_S = "Exception ocurred while updating the hypervisor '%s' on POP '%s'"
Exception_Update_vCDN_S_POP_S = "Exception ocurred while updating the vCDN '%s' on POP '%s'"

Exception_Update_Flavor_S_POP_S = "Exception ocurred while updating the flavors  '%s' on POP '%s' "

Getting_Metric_Pop_D_tenant_S = "Obtaining metrics from POP '%s' for vCDN '%s'"

NoConnect_Pop_S = "Unable to connect and login to POP '%s' "


Exception_Simulating = "Exception occured while running the simulation"


Updated_Pop_S = "Updated information from POP '%s'"

Updated_Tenants_Pop_S = "Updated Tenants instances from POP '%s' "

Updated_Metrics_Pop_S = "Updated Tenants metrics from POP '%s'"
Updated_Metric_Instance_D  = "Updated Metrics of Instance ID %s"
Added_Metric_Instance_D  = "Added Metrics for Instance ID %s"

Found_Instance_S_at_POP_S_LimitsInstances_D = "Found instance of %s at Pop %s with %d VMs "
Deleted_Instance_S_at_POP_S = "Deleted instance of %s at Pop %s "
Added_Instance_S_at_POP_S = "Added instance of %s at Pop %s "
Updated_Instance_S_at_POP_S = "Updated instance of %s at Pop %s"

NoModel = "There is no Model to work with"
NoInstances = "No Instances found in the DB"
NoMigrations = "No Migrations found in the DB"

NoRedirectsSelected = "No Redirections selected"
NoMigrationsSelected = "No Migrations selected"
NoInstantiationsSelected = "No Instantiations selected"

ConnectDB_S = "Connecting to DB with url '%s' "

Simulate_Migration_vCDN_S_from_POP_S_to_POP_S = "Simulate Migration of vcdn '%s' from POP '%s' to POP '%s'"
Simulate_Redirection_vCDN_S_from_POP_S_to_POP_S = "Simulate Redirection of vcdn '%s' from POP '%s' to POP '%s'"
Simulate_Instantiation_vCDN_S_on_POP_S = "Simulate Instantiation of vcdn '%s' on POP '%s' "

Simulating_Instantiations = "Simulating the Instantiations"
Simulated_D_Instantiations = "Simulated %d Instantiations in the Model"
Simulating_Redirections  = "Simulating the Redirections"
Simulated_D_Redirections = "Simulated %d Redirections in the Model"
Simulating_Migrations  = "Simulating the Migrations"
Simulated_D_Migrations = "Simulated %d Migrations in the Model"
Adjusting_Instances_Demands = "Adjusting the Instances and Demands to the selected changes"
Adjusting_Model = "Adjusting the Model's Graph to reflect the simulated Instances"
Running_Demands = "Running the simulated Demands"

###
### OptimizationModels.py
###

Building_Model = "Building a new Model"
Added_Node_S = "Added node %s "
Added_Link_S_to_S_of_D = "Added link from %s to %s, %d Mbps"
Added_Pop_S_in_S = "Added pop %s to node %s"
Added_Client_S_in_S = "Added clientGroup %s to node %s"
Draw_File_S = "Graph drawn to file %s"
Client_S_requests_S_from_S_BW_D = "Demand from ClientGroup at %s requesting vCDN %s from Pop %s with BW %d"
Migration_to_POP_S = "Migration to Pop %s"
NeedeBW_D_more_LinkBW_D =  "The needed BW %d Mbps is more than the available link %d Mbps"

Built_Model_D_locations_D_links = "A new model was built with %d locations and %d links "
Added_D_POPs = "Added %d POPs to the Model"
Added_D_Clients = "Added %d ClientGroups to the Model"

RandomGraph_locationsD_maxCapaD = "Creating random Graph for %d locations with maxCapacity=%d "
RandomGraph_locationsD = "Created random Graph of %d nodes"

Migration_condition_BWNeeded_D_GomuriCap_D_PopCap_PopCanHost_S = "Migration condition: DemandedBW=%d LinkBW=%d PopBW=%d PopCanHost=%s"
ShortestPath_S = "The SPT for this demand is '%s' "
Migrate_vCDN_S_srcPOP_S_dstPOP_S = "Migrate vCDN '%s' from POP '%s' to POP '%s' "
HMAC_optimized_D_migrations_D_invalidDemands = "HMAC optimization determined %d migrations and %d invalid demands"

ClientLocation_S_requests_S_from_S_TotalBW_F = "Clients located in '%s' request vCDN '%s' from POP '%s', needing %.2f Mbps of BW"
Migration_path_D_Hops_F_BW = "Migration path of %d hops and %.2f Mbps minimal BW"
Migration_Condition_Hold_B_NetCapacity_D_Mbps = "The Migration was rejected because HoldvCDN = %s and Remaining BW in POP is %d Mbps"
Scale_Condition_NetCapacity_D_Mbps = "The Scaling was rejected because Remaining BW in POP is %d Mbps"

Migration_check_PopSrc_S_PopDts_S = "Checking possible migration from POP '%s' to POP '%s'"

Graph_Topologie_Consume_Demands = "Consuming a Topologie Graph with a set of demands"
Graph_Capacity_Consume_Demands = "Consuming a Capacity Graph with a set of demands"
Graph_Consume_D_Demands = "Consumed %d Demands from the Graph"
Graph_Return_D_Demands = "Returned %d Demands to the Graph"
Exception_Consuming_Demand_D_Graph = "Exception while consuming Demand %d on a Topologie Graph"
Exception_Removing_Demand_D_Graph = "Exception while returning Demand %d on a Topologie Graph"

Exception_Migrating_vCDN_S_PopSrc_S_PopDts_S = "Exception occured while calculating migration of vCDN '%s' from POP '%s' to POP '%s'"
Redirect_Demand_Client_S_vCDN_S_srcPOP_S_dstPOP_S = "Scale-out and redirect Demands of clientGroup '%s' for vCDN '%s' from POP '%s' to POP '%s'"


Demand_id_D_isValid = "Demand %d has a valid Instace, unable to simulate an Instantiation"
Redirect_D_invalid = "Redirect %d is invalid; could be a Migration"

Errors_simulating = "Some error occured while executing the simulation"

Removing_Simulated_Redirects = "Removing the Demands from the previous path before redirection"
Consuming_Simulated_Redirects = "Adding the Demands on the simulated path after redirection"

Exception_Consuming_Fake_Demand = "Exception occured while Consuming a simulated Demand"
ClientLocation_S_requests_from_S_TotalBW_F = "Consuming fake Demand of ClientGroup at '%s' to POP '%s' with BW '%.2f'"

Deleted_Fake_Instace_POP_S_vCDN_S = "Deleting Fake Instance in POP '%s' of vCDN '%s'"
Added_Fake_Instace_POP_S_vCDN_S = "Adding Fake Instance in POP '%s' of vCDN '%s'"
Update_Fake_Demand_fromPOP_S_toPOP_S = "Update of Demand from POP '%s' to POP '%s'"

Unable_Write_File_S = "Unable to write the file '%s'"
OMAC_DAT_S = "OMAC .dat file was created in '%s'"

###
### OpenStackConnection.py
###


AuthOS_url_S_user_s_tenant_S = "Authenticating to URL %s as User '%s' of Tenant '%s'"
AuthOS_region_S = "Authenticating to Region '%s'"
Exception_Nova_url_S_region_S_user_S_tenant_S = "Unable to authenticate to Nova Service via URL %s in Region '%s' as User '%s' of Tenant '%s'"
Exception_Ceilometer_url_S_region_S_user_S_tenant_S = "Unable to Nova Service via URL %s in Region '%s' as User '%s' of Tenant '%s'"

LastSample_S_at_S = "Last sample of meter '%s' at '%s' "
CollectSamples_S_since_S = "Collecting stats of meter '%s' since '%s' "
Meter_Stats_minD_maxD_avgD = "Values collected are: Min=%d Max=%d Avg=%d "
NoMetrics_Meter_S = "No Metric collected for meter '%s' "
Authenticated = "Authenticated"
