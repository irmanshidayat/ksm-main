def model_to_dict(model, depth=0, max_depth=3, visited=None):
    """Mengkonversi model SQLAlchemy ke dictionary dengan protection terhadap circular reference"""
    if model is None:
        return None
    
    # Protection terhadap infinite recursion
    if depth > max_depth:
        return {"_recursion_limit": "Maximum depth exceeded"}
    
    if visited is None:
        visited = set()
    
    # Protection terhadap circular reference
    model_id = id(model)
    if model_id in visited:
        return {"_circular_reference": "Circular reference detected"}
    
    visited.add(model_id)
    
    if hasattr(model, '__table__'):
        # Single model
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if hasattr(value, 'isoformat'):  # datetime object
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        
        # Handle relationships dengan depth control
        if depth < max_depth:
            for relationship_name in model.__mapper__.relationships.keys():
                if hasattr(model, relationship_name):
                    rel_value = getattr(model, relationship_name)
                    if rel_value is not None:
                        if hasattr(rel_value, '__iter__') and not hasattr(rel_value, '__table__'):
                            # List relationship
                            result[relationship_name] = [model_to_dict(item, depth + 1, max_depth, visited.copy()) for item in rel_value]
                        else:
                            # Single relationship
                            result[relationship_name] = model_to_dict(rel_value, depth + 1, max_depth, visited.copy())
                    else:
                        result[relationship_name] = None
        
        visited.remove(model_id)
        return result
    else:
        # List of models
        return [model_to_dict(item, depth, max_depth, visited) for item in model]

def serialize_models(models):
    """Serialize models untuk response JSON"""
    if isinstance(models, list):
        return [model_to_dict(model) for model in models]
    else:
        return model_to_dict(models)
