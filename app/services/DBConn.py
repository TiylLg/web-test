import pymongo
from app.config.Config import settings


def get_client():
    mongo_server = settings.mongodb_host

    client = pymongo.MongoClient(mongo_server,
                                 username=settings.mongodb_username,
                                 password=settings.mongodb_password,
                                 authSource=settings.mongodb_auth_source,
                                 retryWrites=settings.mongodb_retry_writes
                                 )

    return client


myclient = get_client()
mydb = myclient.get_database(settings.auth_db)

def aggregate(
        collection: str,
        match_query: dict,
        project_fields: list,
        include_id: bool = False
):
    col = mydb[collection]
    project_query = {field: 1 for field in project_fields}
    project_query['_id'] = 1 if include_id else 0

    query = [
        {"$match": match_query},
        {"$project": project_query}
    ]
    cursor = col.aggregate(query)
    res_list = next(cursor, None)
    return res_list

def insert_doc(
        collection: str,
        payload: dict
):
    col = mydb.get_collection(collection)
    col.insert_one(payload)


def upsert_doc(
        collection: str,
        match_query: dict,
        update_data: dict
):
    col = mydb[collection]

    result = col.update_one(
        match_query,
        {"$set": update_data},
        upsert=True
    )

    return result

def calc_doc(
        collection: str,
        match_query: dict,
        operation: dict
):
    col = mydb[collection]

    result = col.update_one(
        match_query,
        operation,
        upsert=True
    )

    return result

def delete_doc(
        collection: str,
        delete_query: dict
):
    col = mydb[collection]
    result = col.delete_one(delete_query)

    return result

def find_doc(
        collection: str,
        find_query: dict,
        include_id: bool = True,
        projection: dict = None
):
    """
    Find a single document matching the query
    
    Args:
        collection: Collection name
        find_query: MongoDB query dictionary
        include_id: Whether to include _id field in results (only used if projection is None)
        projection: Optional projection dict. If None, returns all fields.
        
    Returns:
        Single document or None if not found
    """
    col = mydb[collection]
    
    # If projection is specified, use it
    if projection is not None:
        return col.find_one(find_query, projection)
    
    # If no projection, return all fields (optionally excluding _id)
    if not include_id:
        return col.find_one(find_query, {'_id': 0})
    
    # Return all fields including _id
    return col.find_one(find_query)

def find_docs(
        collection: str,
        query: dict,
        include_id: bool = False
):
    """
    Find multiple documents matching the query
    
    Args:
        collection: Collection name
        query: MongoDB query dictionary
        include_id: Whether to include _id field in results
        
    Returns:
        List of matching documents
    """
    col = mydb[collection]
    projection = {'_id': 1 if include_id else 0}
    cursor = col.find(query, projection)
    return list(cursor)