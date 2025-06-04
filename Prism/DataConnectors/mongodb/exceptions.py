class MongoConnectionError(Exception):
    """Raised when MongoDB connection fails"""
    pass

class MongoQueryError(Exception):
    """Raised when MongoDB query execution fails"""
    pass

class MongoValidationError(Exception):
    """Raised when MongoDB document validation fails"""
    pass

class MongoIndexError(Exception):
    """Raised when MongoDB index operations fail"""
    pass

class MongoAggregationError(Exception):
    """Raised when MongoDB aggregation pipeline fails"""
    pass
