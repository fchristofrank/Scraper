# %%
import pymongo
import json
import requests
import time

# %%
# Global variable for the database
db = None
CONNECTION_STRING = "mongodb+srv://gdb:Nm316PIVSFP3hbFS@gdbproductsc1.ioay5.mongodb.net/admin?replicaSet=atlas-10s7ss-shard-0&readPreference=primary&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1"
COLLECTION_NAME = "CleanedData"   
FIELD_NAME = "ingredientList"
DATABASE_NAME = "GroceryDB"


# %%
def init_db(connection_string, database_name):
    """Initialize the MongoDB connection and set the global db variable."""
    global db
    try:
        client = pymongo.MongoClient(connection_string)
        db = client[database_name]
    except Exception as e:
        print("Error initializing the database:", e)
        
init_db(CONNECTION_STRING,DATABASE_NAME)


# %%
def fetch_field_from_mongo(collection_name, field_name):
    """Fetch a specific field from a MongoDB collection and return as JSON."""
    global db
    if db is None:
        return json.dumps({"error": "Database not initialized. Run init_db cell first."})

    try:
        collection = db[collection_name]
        results = collection.find({}, {field_name: 1, "_id": 0})
        data = [doc.get(field_name, "Field not found") for doc in results]
        return data
    except Exception as e:
        print("The field fetch from DB failed!")
        return 

# %%
def count_response_codes(urls):
    
    """This function will give us the statistic on how many products are currently offered in the respective store."""
    
    status_counts = {"200": 0, "4xx": 0, "5xx": 0, "other": 0, "not_available_products": [] }

    for url in urls:
        try:
            print(url)
            response = requests.get(url, timeout=5)  # Timeout to prevent long waits
            status_code = response.status_code

            if status_code == 200:
                status_counts["200"] += 1
            elif 400 <= status_code < 500:
                status_counts["4xx"] += 1 
                status_counts["not_available_products"].append(url)
            elif 500 <= status_code < 600:
                status_counts["5xx"] += 1 
            else:
                status_counts["other"] += 1 

        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            status_counts["other"] += 1  # Count failed requests

    return status_counts

urls_in_db = fetch_field_from_mongo(COLLECTION_NAME,"url")
count_response_codes(urls_in_db)


# %%
flaggedRecords = []
error_count = 0

def fetch_field_from_mongo(collection_name, field_name):
    """Fetch a specific field from MongoDB."""
    try:
        return [doc[field_name] for doc in db[collection_name].find({field_name: {"$regex": "^tg_"}}, {field_name: 1, '_id': 0}).limit(25)]
    except Exception as e:
        print(f"Error fetching field {field_name} from collection {collection_name}: {e}")
        return []


def get_original_ids():
    """Fetch original IDs from MongoDB"""
    original_ids = fetch_field_from_mongo("CleanedData", "original_ID")
    print("Results",original_ids)
    return original_ids

get_original_ids()

# %%
def build_url(product_id):
    """Construct the API URL using the product ID."""
    base_url = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={}&is_bot=false&pricing_store_id=3324&visitor_id=019347C3E9160201A06B297D0CC373F6"
    return base_url.format(product_id)

def fetch_nutritional_data(url, headers):
    """Make a request to the API and fetch nutritional data."""
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed for URL {url} with status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error while making the request: {e}")
        return None

def extract_nutritional_values(data):
    
    """Extract and format nutritional values from the API response."""
    nutritional_data = {}
    nutrition_facts = data.get('data', {}).get('product', {}).get('item', {}).get('enrichment',{}).get('nutrition_facts',{})
    value_prepared_list = nutrition_facts.get('value_prepared_list', [])
    
    if value_prepared_list:
        nutrients = value_prepared_list[0].get('nutrients', [])
        for nutrient in nutrients:
            name = nutrient.get('name')
            quantity = nutrient.get('quantity')
            unit = nutrient.get('unit_of_measurement')
            if name and quantity is not None:
                nutritional_data[name] = {"quantity": quantity, "unit_of_measurement": unit}

    return nutritional_data

def fetchDataFromMongo(databaseProductID):
    
    try:
        # Target Specific
        databaseProductID = "tg_" + databaseProductID
        record = db[COLLECTION_NAME].find_one({"original_ID": {"$regex": f"^{databaseProductID}$", "$options": "i"}})
    except Exception as e:
        print(f"Error fetching record for original_ID {databaseProductID}: {e}")
    return record
    

def checkForDifference(nutritional_values_current):
    
    DEVIATION_TOLERANCE = 1
    global foodRecords

    for productID in nutritional_values_current.keys():
        try:
            nutritional_values_database = fetchDataFromMongo(productID)
            if not nutritional_values_database:
                flaggedRecords.append(f"tg_{productID}: Database record not found")
                continue

            nutrients_to_check = {
                "Total Fat": "Total Fat Conv",
                "Cholesterol": "Cholesterol Conv",
                "Sodium": "Sodium Conv",
                "Total Carbohydrate": "Carbohydrate Conv",
                "Dietary Fiber": "Fiber, total dietary Conv",
                "Total Sugars": "Sugars, total Conv",
                "Protein": "Protein Conv",
                "Calcium": "Calcium Conv",
                "Iron": "Iron Conv",
                "Calories": "calories Conv",
                "Vitamin A": "Total Vitamin A Conv",
                "Vitamin C": "Vitamin C Conv"
            }

            for nutrient, db_field in nutrients_to_check.items():
                if nutrient in nutritional_values_current[productID]:
                    try:
                        db_value = nutritional_values_database[db_field]
                        if isinstance(db_value, str):
                            db_value = json.loads(db_value)
                        if isinstance(db_value, list):
                            db_value = float(db_value[0])
                        else:
                            db_value = float(db_value)
                        current_value = float(nutritional_values_current[productID][nutrient]["quantity"])

                        if abs(db_value - current_value) > DEVIATION_TOLERANCE:
                            flaggedRecords.append(f"tg_{productID}: {nutrient} deviation (DB: {db_value}, Current: {current_value})")
                            break
                    except (KeyError, ValueError, TypeError) as e:
                        flaggedRecords.append(f"tg_{productID}: Error processing {nutrient} - {e}")
                        break
        except Exception as e:
            flaggedRecords.append(f"tg_{productID}: Error fetching data - {e}")

    print(flaggedRecords)
    
    

def fetch_nutritional_values():
    
    """Main function to fetch and store nutritional values."""
    original_ids = get_original_ids()
    headers = {
        "User-Agent": "PostmanRuntime/7.43.0",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Postman-Token": "b6a248c3-d3e7-42eb-8e0f-e23c3b8fc914",
        "Host": "redsky.target.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": "TealeafAkaSid=Di5RRXbgfIeZiq0-c3T4YQpuPsxcgwHW; sapphire=1; visitorId=0194BE4F07B90201BBFC5093D03D4773"
    }
    nutritional_values = {}
    global foodRecords
    
    for product_id in original_ids:
        try:
            if not product_id.startswith("tg"):
                continue
            new_id = product_id[3:]
            if new_id.isdigit():
                url = build_url(new_id)
                print(f"Making request for URL: {url}")
                
                data = fetch_nutritional_data(url, headers)
                if data:
                    nutritional_values[new_id] = extract_nutritional_values(data)
                time.sleep(5)
        except Exception as e:
            if "Error" in str(e):
                error_count += 1
                if error_count >= 100:
                    print("Error count exceeded 100. Stopping further processing.")
                    break
            flaggedRecords.append(f"Error processing product ID {product_id}: {e}")
            
    checkForDifference(nutritional_values)
    
    return nutritional_values

fetch_nutritional_values()

# %%
for record in flaggedRecords:
    print(f"Flagged Record: {record}")


# %%
def PickUPChange():
    print("Please ignore this Cell")
    pass

# %%



