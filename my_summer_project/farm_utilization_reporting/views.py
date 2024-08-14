from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from .models import *
import json
from .services import *
from datetime import datetime as dt
from hashlib import sha3_512

# Create your views here.
stafAgent = STAFApplicationTool()
stafToDBAssistant = STAFResponseConsumptionAssistant()
validRequests = ValidRequests()
reportAccountant = FarmUtilizationReportingAccount()

def styles(req):
    """
        Styles view: For the '.*/styles/' url. 
        Returns the css used by the table in the list, listpending, & data views.
    """
    response_data = open("farm_utilization_reporting/css/styles.css",'r')
    response_data = response_data.read()
    return HttpResponse(response_data,content_type="text/css")

def listpending(req):
    """
        Listpending view: For the 'listpending/' url. 
        Returns a template that requests data from 'listpendingdata/' and that can render a table using the returned data.
    """    
    queries = req.GET.getlist('q')  # Check for filters the client browser may have requested
    append_data = ""
    if queries: # If there are filters, append them to this variable
        append_data = f"?q={queries[0].replace(' ','')}"
    template = loader.get_template("farm_utilization_reporting/react_library_local_use_only.html")  # Get the template with the REACT table.
    context = {"where_to_get_data":f"listpendingdata{append_data}","var_name":"{listpending_data}","component_list":"<MyTable data={data}/>","components_required_to_do_the_stuff":["farm_utilization_reporting/react_library_local_use_only_table.html"]} # Context map that will populate the template. This tells the front-end where to get data from & what to expect the data to be called.
    return HttpResponse(template.render(context,req))

def listpendingdata(req):
    """
        Listpendingdata view: For the 'listpending/listpendingdata/' url. 
        Returns the Listpending data from the DB as a javascript file to enable quick and easy use by the REACT table. 
    """    
    return_list = []

    queries = req.GET.getlist('q')  # Look for filters to apply
    filters = []
    if queries:
        filters = queries[0].split(',')
    if filters: # If there are filters then apply them here, currently only filters for a single platform and capabilities subset is supported
        LISTPENDINGS = reportAccountant.all_tests.filter(platform=filters[0])
        for i in filters[1::]:
            LISTPENDINGS = LISTPENDINGS.filter(capabilities=i)
        for i in range(len(LISTPENDINGS)):
            if len(LISTPENDINGS[i].capabilities.all()) == len(filters)-1:
                return_list.append(LISTPENDINGS[i].__iter__())
    else:   # No filters. Prepare all data to be returned
        LISTPENDINGS = reportAccountant.all_tests
        for i in LISTPENDINGS:
            return_list.append(i.__iter__())
    return HttpResponse(f"listpending_data=[{json.dumps(return_list)},['handle','platform','pollTimestamp','capabilities']]",content_type="application/javascript") # The response is an array where the first index is the data from the DB and the second index is the labels associated with the DB data.

def clearAndUpdateListPending(req):
    """
        clearAndUpdateListPending view: View for the same named url. Deletes all items in the Listpending model and repopulates it with new data form STAF.
        Returns the Queryset of items added to the model.
    """
    LISTPENDINGS = stafAgent.getSTAFData(["listpending type vatf"]) # Get data from STAF
    stafToDBAssistant.submit_data(LISTPENDINGS[0::2],LISTPENDINGS[1::2])    # Prepare data for DB consumption
    LISTPENDINGS = stafToDBAssistant.response[0]    # Extract the processed data
    reportAccountant.deleteFromDB(listpendings="all")
    time_for_current_push = dt.now()    # Get the time now, use the same time for all items pushed to the table
    polltime_object = PollTimestamp_0_0_1(pollTime=time_for_current_push.__str__())
    polltime_object.save()
    addAllCaps(LISTPENDINGS)
    for i in LISTPENDINGS:  # Iterate through the processed data
        try:
            temp = Listpending_0_1_0(handle=i['handle'],pollTimestamp=polltime_object)    # Create a new Listpending data object with the variables that do not have a ManytoMany relationship
            temp.save() # Save the item to the DB table. Need to do this before adding the variables with ManytoMany relationships
            for j in i['capabilities'].replace('[',"").replace(']',"").replace("'","").split(','):  # Add all the capabilities to the new object.
                temp.capabilities.add(j)
            temp.platform.add(i['platform'])    # Add the platform to the new object
            #temp.pollTimestamp.add(time_for_current_push.__str__())
            temp.save() # Save the updates to the DB table
        except:
            print("failed to create id",file=sys.stderr)
    reportAccountant.updateALLVariables(time_for_current_push)   # Update the public variables created at the beginning of this script
    return HttpResponse(f"{Listpending_0_1_0.objects.all()}",content_type="text/plain") # Return the new table as plaintext

def list(req):
    """
        List view: View for the 'list/' url. 
        Returns a template that requests data from 'listdata/' and that can render a table using the returned data.
    """
    queries = req.GET.getlist('q')  # Check for filters the client browser may have requested
    append_data = ""
    if queries: # If there are filters, append them to this variable
        append_data = f"?q={queries[0].replace(' ','')}"
    template = loader.get_template("farm_utilization_reporting/react_library_local_use_only.html")  # Get the template with the REACT table.
    context = {"where_to_get_data":f"listdata{append_data}","var_name":"{list_data}","component_list":"<MyTable data={data}/>","components_required_to_do_the_stuff":["farm_utilization_reporting/react_library_local_use_only_table.html"]}   # Context map that will populate the template. This tells the front-end where to get data from & what to expect the data to be called.
    return HttpResponse(template.render(context,req))

def listdata(req):
    """
        Listdata view: For the 'list/listdata/' url. 
        Returns the FarmBoard data from the DB as a javascript file to enable quick and easy use by the REACT table.
    """ 
    return_list = []

    queries = req.GET.getlist('q')  # Look for filters to apply
    filters = []
    if queries:
        filters = queries[0].split(',')
    if filters: # If there are filters then apply them here, currently only filters for a single platform and capabilities subset is supported
        FARMBOARDS = FarmBoards_0_0_1.objects.filter(platform__name__istartswith=filters[0])
        if len(filters) > 1:
            for i in filters[1::]:
                FARMBOARDS = FARMBOARDS.filter(capabilities=i)
    else:   # No filters. Prepare all data to be returned
        FARMBOARDS = FarmBoards_0_0_1.objects.all()
    for i in FARMBOARDS:
        return_list.append(i.__iter__())
    return HttpResponse(f"list_data=[{json.dumps(return_list)},['name_type','platform','active','capabilities']]",content_type="application/javascript")    # The response is an array where the first index is the data from the DB and the second index is the labels associated with the DB data.

def clearAndUpdateList(req):
    """
        clearAndUpdateList view: View for the same named url. Deletes all the items in the FarmBoards model and repopulates it with new data from STAF.
    """ 
    reportAccountant.hash_of_last_list_pull   # Import this variable from the global scope to be allowed to keep it up to date after repopulating the table.
    FARMBOARDS = stafAgent.getSTAFData(["list"])    # Get data from STAF
    stafToDBAssistant.submit_data(FARMBOARDS[0::2],FARMBOARDS[1::2])    # Prepare data for DB consumption
    FARMBOARDS = stafToDBAssistant.response[0]  # Extract the processed data
    FarmBoards_0_0_1.objects.all().delete() # Delete the items in the DB table
    time_for_current_push = dt.now()    # Get the time now, use the samme time for all items pushed to the table
    addAllCaps(FARMBOARDS) 
    list_of_boards_to_return = []
    reportAccountant.hash_of_last_list_pull = sha3_512(bytes(str(FARMBOARDS),encoding='UTF-8'))  # Update the global hash of the last list pull now.
    for i in FARMBOARDS:    # Iterate through the processed data
        try:
            list_of_caps_to_add = i['capabilities'].replace('[',"").replace(']',"").replace("'","").split(',')  # Extract the capabilities from the response string
            temp = FarmBoards_0_0_1(name_type=i['name_type'],added_datetime=time_for_current_push)  # Create a new FarmBoards data object with the variables that do not have a ManytoMany relationship
            temp.save() # Save the item to the DB table. Need to do this before adding the variables with ManytoMany relationships
            for j in list_of_caps_to_add:   # Add all the capabilities to the new object
                temp.capabilities.add(j)
            temp.platform.add(i['platform'])    # Add the platform to the new object
            temp.save() # Save the updates to the DB table
            list_of_boards_to_return.append(temp)
        except:
            print("failed to create id",file=sys.stderr)
    reportAccountant.updateALLVariables(time_for_current_push)   # Update the public variables created at the beginning of this script
    return HttpResponse(f"{list_of_boards_to_return}",content_type="text/plain")    # Return the new table as plaintext

def addAllCaps(json_data:list, CODE:int = 0) -> None:
    """
    addAllCaps function: A helper function. Its sole purpose is to add capabilities to the capabilities DB table.
        Args:
            json_data: A list of data from a STAF response. You can pass an index from the STAFResponseConsumptionAssistant response variable
            CODE: A value of 0 indicates that there is only 1 set of data in json_data. A value other than 0 indicates that multiple datasets are found in json_data
    """
    caps_found = []
    if CODE:    # Multiple STAF responses are in json_data
        for i in json_data: # Iterate through the data sets
            for j in i: # For each item in the data sets, extract the capabilities & the platform and try to push them to their DB tables. If it fails, move on to the next data item.
                extracted_caps = j['capabilities'].replace('[',"").replace(']',"").replace("'","").split(',')
                extracted_platform = j['platform']
                try:
                    Platforms_0_0_1.objects.create(name=extracted_platform)
                except:
                    pass
                    #print("Failed to add platform:\t",extracted_platform)
                for k in extracted_caps:
                    try:
                        Capabilities_0_0_1.objects.create(name=k)
                    except:
                        pass
                        #print("Failed to add cap:\t",k)
    else:   # Only one STAF response is in json_data
        for i in json_data: # Iterate through the data set. Extract the capabilities & the platform and try to push them to their DB tables. If it fails, move on to the next data item.
            extracted_caps = i['capabilities'].replace('[',"").replace(']',"").replace("'","").split(',')
            extracted_platform = i['platform']
            try:
                Platforms_0_0_1.objects.create(name=extracted_platform)
            except:
                pass
                #print("Failed to add platform:\t",extracted_platform)
            for k in extracted_caps:
                try:
                    Capabilities_0_0_1.objects.create(name=k)
                except:
                    pass
                    #print("Failed to add cap:\t",k)

def data(req):
    """
        Data view: For the 'data/' url. 
        Returns a template rednered with values indicating where it should get data from, what the data will be named, what react components to render, & where to get the components from.
    """    
    platforms = req.GET.getlist('pl')  # Look for filters to apply
    global_capabilities = req.GET.getlist('gc')  # Look for filters to apply
    dates_req = req.GET.getlist('dates')  # Look for filters to apply
    append_data = ""
    if platforms: # If there are filters, append them to this variables
        append_data += f"?pl={'&'.join(platforms)}&"
    if global_capabilities:
        append_data += f"?gc={'&'.join(global_capabilities)}&"
    if dates_req:
        append_data += f"?dates={'&'.join(dates_req)}"
    template = loader.get_template("farm_utilization_reporting/react_library_local_use_only.html")  # Get the template with the REACT table
    context = {"where_to_get_data":f"datadata{append_data}","var_name":"{data_data}","component_list":f'<MyMenu data={{[data[0],data[1],data[3]]}}/><MyTable data={{JSON.parse(data[2]).response}}/>',"components_required_to_do_the_stuff":["farm_utilization_reporting/react_library_local_use_only_menu.html","farm_utilization_reporting/react_library_local_use_only_table.html"]}   # Context map that will populate the template. This tells the front-end where to get data from & what to expect the data to be called.
    return HttpResponse(template.render(context,req))

def datadata(req):
    """
        Datadata view: For the 'data/datadata/' url. 
        Returns data to populate a react based table in the form of a JavaScript file.
    """    
    myplats = Platforms_0_0_1.objects.all()
    mycaps = Capabilities_0_0_1.objects.all()
    mydates = []
    for i in reportAccountant.all_dates:
        if i not in mydates:
            mydates.append(i)
    platform_names = []
    capability_names = []
    for i in myplats:
        platform_names.append(i.name)
    for i in mycaps:
        capability_names.append(i.name)
    return HttpResponse(f"data_data=[{platform_names},{capability_names},{data_dep(req)},{mydates}]",content_type="application/javascript")  # Return the list of dictionaries of data and the labels associated with the data

def data_dep(req):
    """
        Data view: For the 'data/' url. 
        Returns data that can be accepted by a react based table in the form of a string.
    """
    return json.dumps(data_helper_function(req))  # Return the list of dictionaries of data and the labels associated with the data

def datadata_dep(req):
    """
        Datadata view: For the 'data/datadata/' url. 
        Returns the string from @data_helper_function as a json HTTP response.
    """
    return HttpResponse((data_helper_function(req)),content_type="application/json")  # Return the list of dictionaries of data and the labels associated with the data

def cronJobView(req):
    """
        CronJobView view: For the 'cronPoint/' url. Gets new 'list' & 'listpending type vatf' data from STAF & pushes it to the DB.
        Return 'OK 200'.
    """
    newData = stafAgent.getSTAFData(["list", "listpending type vatf"])  # Get 'list' & 'listpending' data from STAF
    stafToDBAssistant.submit_data(newData[0::2],newData[1::2])  # Prepare data for DB consumption
    newData = stafToDBAssistant.response
    time_for_current_push = dt.now()    # Get the time now. Use this time all boards/tests added to DB in this cycle.
    polltime_object = PollTimestamp_0_0_1(pollTime=time_for_current_push.__str__())
    polltime_object.save()
    list_of_boards_to_return = []
    addAllCaps(newData,1)   # Add all capabilities found in the responses from 'list' & 'listpending'. Need to do this here to ensure that we do not get a 'foreign key' error later.
    reportAccountant.validateBoardsExist(time_for_current_push,newData[0])   # Ensure all previously active boards are still active.
    print("About to cronJOB list")  
    for i in newData[0]:    # Iterate through all boards in response
            try:
                    temp = FarmBoards_0_0_1(name_type=i['name_type'],added_datetime=time_for_current_push)  # Create new board object with variables w/out Many2Many relationships
                    temp.save() # Save to DB
                    list_of_caps_to_add = i['capabilities'].replace('[',"").replace(']',"").replace("'","").split(',')  # Extract the capabilities from the capabilities string
                    for j in list_of_caps_to_add:   # Add each capability to the board object
                        temp.capabilities.add(j)
                    temp.platform.add(i['platform'])    # Add the platform to the board object
                    temp.save() # Update the object in the DB with the capabilities & platform update.
                    list_of_boards_to_return.append(temp)
            except ValueError as ve:
                print("[Views: cronJobView] ",ve,"failed to create id",file=sys.stderr)
            except Exception as e:
                print("[Views: cronJobView] ",e,"failed to create id",file=sys.stderr)
                 
    print("About to cronJOB listpending")
    reportAccountant.updateALLVariables(time_for_current_push)   # Update the global scope variables.
    for i in newData[1]:    # Iterate through the list of tests pending
            try:
                    temp = Listpending_0_1_0(handle=i['handle'],pollTimestamp=polltime_object)    # Create new test object with variables w/out Many2Many relationships
                    temp.save() # Save to DB
                    for j in i['capabilities'].replace('[',"").replace(']',"").replace("'","").split(','):  # Add each capability to the test object
                        temp.capabilities.add(j)
                    temp.platform.add(i['platform'])    # Add the platform to the test object
                    temp.save() # Update the object in the DB with the capabilities & platform update.
            except:
                    print("failed to create id",file=sys.stderr)
    reportAccountant.updateALLVariables(time_for_current_push)  # Update the global scope variables.
    return HttpResponse(f"OK 200",content_type="text/plain")

def data_helper_function(req):
    platforms = req.GET.getlist('pl')  # Look for filters to apply
    global_capabilities = req.GET.getlist('gc')  # Look for filters to apply
    dates_req:list = req.GET.getlist('dates')  # Look for filters to apply
    filters = False
    execution_time_tracking_list = []   #should be - [[caps_string#1,et#1,et#2,...]]
                                        # Execution time is Poll_frequency / ( ( ( Current_list_size - items_not_in_the_previous_list ) - previous_list_size ) / Number_of_boards_satisfying )
    prev_caps_list = []
    next_caps_list = []
    count_for_capabilities = []
    number_to_average_over = 1
    if platforms or global_capabilities or dates_req:
        filters = True
    if filters: # If there are filters then apply them here, currently only filters for a single platform and capabilities subset is supported
        LISTPENDINGS = reportAccountant.all_tests.all()
        mydates = reportAccountant.all_dates
        if dates_req:
            for i in dates_req:
                i = PollTimestamp_0_0_1.objects.filter(pollTime=i)[0]
            if len(dates_req) == 1:
                LISTPENDINGS = LISTPENDINGS.filter(pollTimestamp__lte=dates_req[0])
                mydates = reportAccountant.all_dates[0:reportAccountant.all_dates.index(dates_req[0].__str__())+1]
            else:
                LISTPENDINGS = LISTPENDINGS.filter(pollTimestamp__gte=dates_req[0]).filter(pollTimestamp__lte=dates_req[-1])
                mydates = reportAccountant.all_dates[reportAccountant.all_dates.index(dates_req[0].__str__()):reportAccountant.all_dates.index(dates_req[-1].__str__())+1]
        for date in mydates:
            LISTPENDINGS_FOR_A_DATE = LISTPENDINGS.filter(pollTimestamp=PollTimestamp_0_0_1(pollTime=date))
            mytests = []
            mycaps_list = []
            if platforms:
                for i in platforms:
                    LISTPENDINGS_FOR_A_DATE_FOR_A_PLATFORM = LISTPENDINGS_FOR_A_DATE.filter(platform=i)    #may cause race condition. I'm sure the server software takes care of it.
                    if LISTPENDINGS_FOR_A_DATE_FOR_A_PLATFORM:    # If tests exist, append them to this variables
                        mytests.append(LISTPENDINGS_FOR_A_DATE_FOR_A_PLATFORM)
                for i in global_capabilities:
                    for j in range(len(mytests)):
                        LISTPENDINGS_FOR_A_DATE = mytests[j].filter(capabilities=i)    #may cause race condition. I'm sure the server software takes for it.
                        mytests[j] = (LISTPENDINGS_FOR_A_DATE)
                for i in mytests:   # Extract capabilities from the tests
                    for j in i:
                        mycaps_str = []
                        mycaps_str.append(str(j.platform.all()[0]))
                        for k in j.capabilities.all():
                            mycaps_str.append(str(k))
                        mycaps_list.append(", ".join(mycaps_str))
                for i in LISTPENDINGS_FOR_A_DATE:
                    if i.pollTimestamp.__str__() not in mydates:
                        mydates.append(i.pollTimestamp.__str__())
                number_to_average_over = len(mydates)

                total_number_of_tests = len(mytests)
                if total_number_of_tests:   # If there are tests, then build the returned data
                    if len(mycaps_list):
                        prev_platform = None
                        current_platform = -1    # Currently looking into the first platform
                        TESTS_MODE = not isinstance(mytests[0],type(reportAccountant.all_tests))
                        while mycaps_list:   # Iterate through all the capabilities
                            boards_satisfying = FarmBoards_0_0_1.objects.all()
                            current_set_of_capabilities = mycaps_list.pop()  
                            number_of_matches = mycaps_list.count(current_set_of_capabilities)   # Count how many times the current set of capabilities was requested by tests
                            temp = current_set_of_capabilities.split(", ")[0]
                            if temp != prev_platform:   # If the current set of capabilities does not equal the previous set of capabilities then assign it the prev variable and increment the platform counter
                                prev_platform = temp
                                current_platform += 1
                            boards_satisfying = boards_satisfying.filter(platform=temp).filter(added_datetime__lte=date, modified_datetime=None) |  boards_satisfying.filter(platform=temp).filter(added_datetime__lte=date, modified_datetime__gt=date)# Get boards with current platform
                            for i in current_set_of_capabilities.split(", ")[1::]:  # Get boards with at least this set of capabilities
                                if not(i == ""):
                                    boards_satisfying = boards_satisfying.filter(capabilities=i)
                            found_the_capabilities = False
                            for item in count_for_capabilities:
                                if item["Capabilities Required for this set of tests"] == f"{current_set_of_capabilities}":
                                    found_the_capabilities = True
                                    item["Number of tests requesting this set of capabilities PER 5 minutes"] = f'{((float(item["Number of tests requesting this set of capabilities PER 5 minutes"])*number_to_average_over)+(1+number_of_matches))/number_to_average_over}'
                                    item["Number of boards satisfying the requirements"] = f'{((float(item["Number of boards satisfying the requirements"])*number_to_average_over)+(len(boards_satisfying)))/number_to_average_over}'
                                    item["% of total tests this set makes up"] = f'{float(item["% of total tests this set makes up"])+((float(1+number_of_matches)/float(total_number_of_tests))*100.) if TESTS_MODE else ((float(1+number_of_matches)/float(len(mytests[current_platform]))*100.)):.4f}'
                                    break
                            if not found_the_capabilities:
                                count_for_capabilities.append({"Capabilities Required for this set of tests":f"{current_set_of_capabilities}","Number of tests requesting this set of capabilities PER 5 minutes":f"{(1+number_of_matches)/number_to_average_over}","Number of boards satisfying the requirements":f"{len(boards_satisfying)/number_to_average_over}","% of total tests this set makes up":f"{((float(1+number_of_matches)/float(total_number_of_tests))*100.) if TESTS_MODE else ((float(1+number_of_matches)/float(len(mytests[current_platform]))*100.)):.4f}"}) # Append to the response
                            for i in range(number_of_matches):
                                mycaps_list.remove(current_set_of_capabilities)  # Remove the evaluated item from the list
                            
                            if current_set_of_capabilities in prev_caps_list:
                                for caps_set in execution_time_tracking_list:
                                    if caps_set[0] == current_set_of_capabilities:
                                        caps_set[-1] += 1
                            else:
                                found_the_capabilities = False
                                for caps_set in range(len(execution_time_tracking_list)):
                                    if execution_time_tracking_list[caps_set][0] == current_set_of_capabilities:
                                        found_the_capabilities = [True,caps_set]
                                        break
                                if found_the_capabilities:
                                    execution_time_tracking_list[found_the_capabilities[1]].append(1)
                                else:
                                    execution_time_tracking_list.append([current_set_of_capabilities,1])
                            next_caps_list.append(current_set_of_capabilities)
                        prev_caps_list = next_caps_list.copy()
                        next_caps_list = []
            elif global_capabilities:
                mytests.append(LISTPENDINGS_FOR_A_DATE)
                for i in range(len(mytests)):
                    for j in global_capabilities:
                        LISTPENDINGS_FOR_A_DATE = mytests[i].filter(capabilities=j)    #may cause race condition. I'm sure the server software takes care of it.
                        mytests[i] = LISTPENDINGS_FOR_A_DATE
                for i in mytests:   # Extract capabilities from the tests
                    for j in i:
                        mycaps_str = []
                        mycaps_str.append(str(j.platform.all()[0]))
                        for k in j.capabilities.all():
                            mycaps_str.append(str(k))
                        mycaps_list.append(", ".join(mycaps_str))
                for i in LISTPENDINGS_FOR_A_DATE:
                    if i.pollTimestamp.__str__() not in mydates:
                        mydates.append(i.pollTimestamp.__str__())
                number_to_average_over = len(mydates)
                total_number_of_tests = len(mytests[0])

                if total_number_of_tests:   # If there are tests, then build the returned data
                    if len(mycaps_list):
                        prev_platform = None
                        current_platform = -1    # Currently looking into the first platform
                        TESTS_MODE = not isinstance(mytests[0],type(reportAccountant.all_tests))
                        while mycaps_list:   # Iterate through all the capabilities
                            boards_satisfying = reportAccountant.all_active_boards
                            current_set_of_capabilities = mycaps_list.pop()  
                            number_of_matches = mycaps_list.count(current_set_of_capabilities)   # Count how many times the current set of capabilities was requested by tests
                            temp = current_set_of_capabilities.split(", ")[0]
                            if temp != prev_platform:   # If the current set of capabilities does not equal the previous set of capabilities then assign it the prev variable and increment the platform counter
                                prev_platform = temp
                                current_platform += 1
                            boards_satisfying = boards_satisfying.filter(platform=temp) # Get boards with current platform
                            for i in current_set_of_capabilities.split(", ")[1::]:  # Get boards with at least this set of capabilities
                                if not(i == ""):
                                    boards_satisfying = boards_satisfying.filter(capabilities=i)
                            found_the_capabilities = False
                            for item in count_for_capabilities:
                                if item["Capabilities Required for this set of tests"] == f"{current_set_of_capabilities}":
                                    found_the_capabilities = True
                                    item["Number of tests requesting this set of capabilities PER 5 minutes"] = f'{((float(item["Number of tests requesting this set of capabilities PER 5 minutes"])*number_to_average_over)+(1+number_of_matches))/number_to_average_over}'
                                    item["Number of boards satisfying the requirements"] = f'{((float(item["Number of boards satisfying the requirements"])*number_to_average_over)+(len(boards_satisfying)))/number_to_average_over}'
                                    item["% of total tests this set makes up"] = f'{float(item["% of total tests this set makes up"])+((float(1+number_of_matches)/float(total_number_of_tests))*100.) if TESTS_MODE else ((float(1+number_of_matches)/float(len(mytests[0]))*100.)):.4f}'
                                    break
                            if not found_the_capabilities:
                                count_for_capabilities.append({"Capabilities Required for this set of tests":f"{current_set_of_capabilities}","Number of tests requesting this set of capabilities PER 5 minutes":f"{(1+number_of_matches)/number_to_average_over}","Number of boards satisfying the requirements":f"{len(boards_satisfying)/number_to_average_over}","% of total tests this set makes up":f"{((float(1+number_of_matches)/float(total_number_of_tests))*100.) if TESTS_MODE else ((float(1+number_of_matches)/float(len(mytests[0]))*100.)):.4f}"}) # Append to the response
                            for i in range(number_of_matches):
                                mycaps_list.remove(current_set_of_capabilities)  # Remove the evaluated item from the list
                            
                            
                            if current_set_of_capabilities in prev_caps_list:
                                for caps_set in execution_time_tracking_list:
                                    if caps_set[0] == current_set_of_capabilities:
                                        caps_set[-1] += 1
                            else:
                                found_the_capabilities = False
                                for caps_set in range(len(execution_time_tracking_list)):
                                    if execution_time_tracking_list[caps_set][0] == current_set_of_capabilities:
                                        found_the_capabilities = [True,caps_set]
                                        break
                                if found_the_capabilities:
                                    execution_time_tracking_list[found_the_capabilities[1]].append(1)
                                else:
                                    execution_time_tracking_list.append([current_set_of_capabilities,1])
                            next_caps_list.append(current_set_of_capabilities)
                        prev_caps_list = next_caps_list.copy()
                        next_caps_list = []
    print(execution_time_tracking_list)
    return_value = None
    if not count_for_capabilities:
        return_value = f'{{"response":[[],["Capabilities Required for this set of tests","Number of tests requesting this set of capabilities PER 5 minutes","Number of boards satisfying the requirements","% of total tests this set makes up"]]}}'
    else:
        return_value = f'{{"response":[{json.dumps(count_for_capabilities)},["Capabilities Required for this set of tests","Number of tests requesting this set of capabilities PER 5 minutes","Number of boards satisfying the requirements","% of total tests this set makes up"]]}}'
    return return_value

def deleteAll(req):
    """
        deleteAll view: For the 'justDeleteAll/' url. Delets the entire contents of the DB. This include the Platform, FarmBoards, Listpendings, & Capabilities models.
        Returns 'OK 200'.
    """
    reportAccountant.deleteFromDB(all=True)
    return HttpResponse("OK 200",content_type="text/plain")