from dataclasses import asdict, is_dataclass
import datetime, json

def obj_to_dict(obj):
    if is_dataclass(obj):
        return asdict(obj)
    elif hasattr(obj, '__dict__'):
        return {k: obj_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple)):
        return [obj_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: obj_to_dict(v) for k, v in obj.items()}
    return obj

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__') or is_dataclass(obj):
            return obj_to_dict(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)