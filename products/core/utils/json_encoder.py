import json
from decimal import Decimal
from datetime import date, datetime


class DecimalEncoder(json.JSONEncoder):
    """JSONEncoder personalizado que maneja Decimal, datetime y date"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convertir Decimal a float o string
            return float(obj)  # o str(obj) si quieres precisión exacta
        elif isinstance(obj, (datetime, date)):
            # Convertir fechas a string ISO format
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):  # Si el objeto tiene método to_dict
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):  # Si es un objeto con atributos
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}

        # Llamar al método por defecto para otros tipos
        return super().default(obj)