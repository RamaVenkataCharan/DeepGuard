"""
Custom Request Parameter Validators.
"""
import re
from marshmallow import ValidationError

def validate_customer_code(value):
    """
    Ensures customer codes follow the CUST-XXXX format.
    """
    if not re.match(r"^CUST-\d+$", value):
        raise ValidationError("Customer code must be in the format CUST-XXXX.")
        
def validate_meter_number(value):
    """
    Ensures meter numbers follow the SM-YYYY-XXXXX format.
    """
    if not re.match(r"^SM-\d{4}-\d+$", value):
        raise ValidationError("Meter number must be in the format SM-YYYY-XXXXX.")
