"""
Customer Management and Readings History API.
Exposes CRUD on customers and lists daily consumption arrays.
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields
from app.models.customer import Customer, Meter
from app.models.meter_reading import MeterReading
from app.extensions import db

customers_blp = Blueprint("customers", "customers", url_prefix="/api/customers", description="Customer operations")

class CustomerSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_code = fields.Str(required=True)
    name = fields.Str(required=True)
    address = fields.Str(required=False)
    region = fields.Str(required=True)
    city = fields.Str(required=False)
    account_status = fields.Str(required=False)
    connection_type = fields.Str(required=False)

@customers_blp.route("/")
class CustomersView(MethodView):
    
    @jwt_required()
    @customers_blp.response(200, CustomerSchema(many=True))
    def get(self):
        """Lists all registered customers in the database."""
        return Customer.query.all()

    @jwt_required()
    @customers_blp.arguments(CustomerSchema)
    @customers_blp.response(201, CustomerSchema)
    def post(self, customer_data):
        """Creates a new customer account profile."""
        if Customer.query.filter_by(customer_code=customer_data["customer_code"]).first():
            abort(400, message="Customer code already exists.")
            
        customer = Customer(**customer_data)
        db.session.add(customer)
        db.session.commit()
        return customer

@customers_blp.route("/<int:customer_id>")
class CustomerDetailsView(MethodView):
    
    @jwt_required()
    @customers_blp.response(200, CustomerSchema)
    def get(self, customer_id):
        """Retrieves details for a specific customer."""
        return Customer.query.get_or_404(customer_id)

    @jwt_required()
    @customers_blp.arguments(CustomerSchema)
    @customers_blp.response(200, CustomerSchema)
    def put(self, customer_data, customer_id):
        """Updates properties of a customer profile."""
        customer = Customer.query.get_or_404(customer_id)
        for key, value in customer_data.items():
            setattr(customer, key, value)
        db.session.commit()
        return customer

    @jwt_required()
    def delete(self, customer_id):
        """Removes a customer account from database tracking."""
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        return {"message": "Customer deleted successfully."}, 200

@customers_blp.route("/<int:customer_id>/consumption")
class CustomerConsumptionView(MethodView):
    
    @jwt_required()
    def get(self, customer_id):
        """Fetches historical time series consumption measurements for a customer."""
        readings = MeterReading.query.filter_by(customer_id=customer_id)\
            .order_by(MeterReading.timestamp.asc()).all()
            
        return {
            "customer_id": customer_id,
            "readings": [r.to_dict() for r in readings]
        }, 200
