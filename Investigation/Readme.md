
1. Objective :  Check if the nutritional data are consistent with the current data in target and the data in grocery DB.

Solution:

1. Make calls to Target Backend
    Get all Nutrional data
    Check if Grocery DB has that field
    if Yes, then compare the value
    Flag it if values are different


Challenge : Discovery Servers is not allowing outbound network traffic to DB?

WorkAround : Taking the CSV dump of grocery DB and modifying the code in the file "DiscoveryVersion" to fetch from csv.s