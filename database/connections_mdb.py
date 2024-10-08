import pymongo
from sample_info import tempDict
from info import DATABASE_URI, DATABASE_NAME, SECONDDB_URI
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Initialize MongoDB clients and collections
myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
mycol = mydb['CONNECTION']

myclient2 = pymongo.MongoClient(SECONDDB_URI)
mydb2 = myclient2[DATABASE_NAME]
mycol2 = mydb2['CONNECTION']

async def add_connection(group_id, user_id):
    """
    Add a connection for a user to the appropriate MongoDB collection.
    """
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "active_group": 0})
        if query is not None:
            group_ids = [x["group_id"] for x in query.get("group_details", [])]
            if group_id in group_ids:
                return False

        group_details = {"group_id": group_id}
        data = {'_id': user_id, 'group_details': [group_details], 'active_group': group_id}

        if mycol.count_documents({"_id": user_id}) == 0 and mycol2.count_documents({"_id": user_id}) == 0:
            if tempDict['indexDB'] == DATABASE_URI:
                mycol.insert_one(data)
            else:
                mycol2.insert_one(data)
        else:
            if mycol.count_documents({"_id": user_id}) == 0:
                mycol2.update_one({'_id': user_id}, {"$push": {"group_details": group_details}, "$set": {"active_group": group_id}})
            else:
                mycol.update_one({'_id': user_id}, {"$push": {"group_details": group_details}, "$set": {"active_group": group_id}})
        
        return True
    except Exception as e:
        logger.exception('Some error occurred while adding connection!', exc_info=True)
        return False

async def active_connection(user_id):
    """
    Get the active connection (group_id) for a user from the appropriate MongoDB collection.
    """
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        query2 = mycol2.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})

        if not query and not query2:
            return None
        elif query:
            return int(query.get('active_group')) if query.get('active_group') else None
        else:
            return int(query2.get('active_group')) if query2.get('active_group') else None
    except Exception as e:
        logger.exception('Some error occurred while retrieving active connection!', exc_info=True)
        return None

async def all_connections(user_id):
    """
    Get all connections (group_ids) for a user from the appropriate MongoDB collection.
    """
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "active_group": 0, "group_details.group_id": 1})
        query2 = mycol2.find_one({"_id": user_id}, {"_id": 0, "active_group": 0, "group_details.group_id": 1})

        if query:
            return [x["group_id"] for x in query.get("group_details", [])]
        elif query2:
            return [x["group_id"] for x in query2.get("group_details", [])]
        else:
            return None
    except Exception as e:
        logger.exception('Some error occurred while retrieving all connections!', exc_info=True)
        return None

async def if_active(user_id, group_id):
    """
    Check if a specific group_id is the active connection for a user in the appropriate MongoDB collection.
    """
    try:
        query = mycol.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        if not query:
            query = mycol2.find_one({"_id": user_id}, {"_id": 0, "group_details": 0})
        return query and query.get('active_group') == group_id
    except Exception as e:
        logger.exception('Some error occurred while checking if active!', exc_info=True)
        return False

async def make_active(user_id, group_id):
    """
    Set a specific group_id as the active connection for a user in the appropriate MongoDB collection.
    """
    try:
        update = mycol.update_one({'_id': user_id}, {"$set": {"active_group": group_id}})
        if update.modified_count == 0:
            update = mycol2.update_one({'_id': user_id}, {"$set": {"active_group": group_id}})
        return update.modified_count != 0
    except Exception as e:
        logger.exception('Some error occurred while making active!', exc_info=True)
        return False

async def make_inactive(user_id):
    """
    Remove the active connection for a user in the appropriate MongoDB collection.
    """
    try:
        update = mycol.update_one({'_id': user_id}, {"$set": {"active_group": None}})
        if update.modified_count == 0:
            update = mycol2.update_one({'_id': user_id}, {"$set": {"active_group": None}})
        return update.modified_count != 0
    except Exception as e:
        logger.exception('Some error occurred while making inactive!', exc_info=True)
        return False

async def delete_connection(user_id, group_id):
    """
    Delete a specific group_id connection for a user from the appropriate MongoDB collection.
    """
    try:
        update = mycol.update_one({"_id": user_id}, {"$pull": {"group_details": {"group_id": group_id}}})
        if update.modified_count == 0:
            update = mycol2.update_one({"_id": user_id}, {"$pull": {"group_details": {"group_id": group_id}}})
            if update.modified_count == 0:
                return False
            else:
                query = mycol2.find_one({"_id": user_id})
                if len(query.get("group_details", [])) >= 1:
                    if query.get('active_group') == group_id:
                        prvs_group_id = query["group_details"][-1]["group_id"]
                        mycol2.update_one({'_id': user_id}, {"$set": {"active_group": prvs_group_id}})
                else:
                    mycol2.update_one({'_id': user_id}, {"$set": {"active_group": None}})
                return True
        else:
            query = mycol.find_one({"_id": user_id})
            if len(query.get("group_details", [])) >= 1:
                if query.get('active_group') == group_id:
                    prvs_group_id = query["group_details"][-1]["group_id"]
                    mycol.update_one({'_id': user_id}, {"$set": {"active_group": prvs_group_id}})
            else:
                mycol.update_one({'_id': user_id}, {"$set": {"active_group": None}})
            return True
    except Exception as e:
        logger.exception('Some error occurred while deleting connection!', exc_info=True)
        return False
