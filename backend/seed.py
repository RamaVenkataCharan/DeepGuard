import sys
from pathlib import Path
from datetime import datetime, date

# Add backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.customer import Customer, Meter
from app.models.meter_reading import MeterReading
from app.models.prediction import Prediction
from app.models.alert import Alert

app = create_app()

def seed_database():
    with app.app_context():
        print("Recreating database tables...")
        db.drop_all()
        db.create_all()
        
        # 1. Seed Users
        print("Seeding Users...")
        admin = User(email='admin@deepguard.io', full_name='System Admin', role='admin')
        admin.set_password('admin123')
        
        analyst = User(email='analyst@deepguard.io', full_name='Jane Analyst', role='analyst')
        analyst.set_password('analyst123')
        
        viewer = User(email='viewer@deepguard.io', full_name='John Viewer', role='viewer')
        viewer.set_password('viewer123')
        
        db.session.add_all([admin, analyst, viewer])
        db.session.commit()
        
        # 2. Seed Customers
        print("Seeding Customers...")
        customers = [
            Customer(id=1, customer_code='CUST-001', name='Rajesh Kumar', address='45 MG Road, Sector 12', region='North Delhi', city='New Delhi', account_status='active', connection_type='residential'),
            Customer(id=2, customer_code='CUST-002', name='Priya Sharma', address='123 Gandhi Nagar, Block B', region='South Delhi', city='New Delhi', account_status='active', connection_type='residential'),
            Customer(id=3, customer_code='CUST-003', name='TechPark Solutions', address='500 IT Park, Phase II', region='Gurgaon', city='Gurgaon', account_status='active', connection_type='commercial'),
            Customer(id=4, customer_code='CUST-004', name='Amit Patel', address='78 Nehru Colony', region='East Delhi', city='New Delhi', account_status='active', connection_type='residential'),
            Customer(id=5, customer_code='CUST-005', name='GreenLeaf Textiles', address='200 Industrial Area, Plot 15', region='Noida', city='Noida', account_status='active', connection_type='industrial'),
            Customer(id=6, customer_code='CUST-006', name='Sunita Verma', address='33 Laxmi Nagar, Flat 4C', region='East Delhi', city='New Delhi', account_status='active', connection_type='residential'),
            Customer(id=7, customer_code='CUST-007', name='Metro Mall Complex', address='1 Central Avenue', region='South Delhi', city='New Delhi', account_status='active', connection_type='commercial'),
            Customer(id=8, customer_code='CUST-008', name='Vikram Singh', address='90 Saket, J Block', region='South Delhi', city='New Delhi', account_status='suspended', connection_type='residential'),
            Customer(id=9, customer_code='CUST-009', name='Ananya Reddy', address='15 Jubilee Hills', region='Hyderabad', city='Hyderabad', account_status='active', connection_type='residential'),
            Customer(id=10, customer_code='CUST-010', name='SteelWorks Ltd.', address='400 MIDC Industrial Estate', region='Pune', city='Pune', account_status='active', connection_type='industrial')
        ]
        db.session.add_all(customers)
        db.session.commit()
        
        # 3. Seed Meters
        print("Seeding Meters...")
        meters = [
            Meter(id=1, customer_id=1, meter_number='SM-2024-00001', meter_type='smart', install_date=date(2023, 1, 15), is_active=True),
            Meter(id=2, customer_id=2, meter_number='SM-2024-00002', meter_type='smart', install_date=date(2023, 2, 20), is_active=True),
            Meter(id=3, customer_id=3, meter_number='SM-2024-00003', meter_type='smart', install_date=date(2023, 3, 10), is_active=True),
            Meter(id=4, customer_id=4, meter_number='SM-2024-00004', meter_type='smart', install_date=date(2023, 4, 5), is_active=True),
            Meter(id=5, customer_id=5, meter_number='SM-2024-00005', meter_type='smart', install_date=date(2023, 5, 12), is_active=True),
            Meter(id=6, customer_id=6, meter_number='SM-2024-00006', meter_type='smart', install_date=date(2023, 6, 1), is_active=True),
            Meter(id=7, customer_id=7, meter_number='SM-2024-00007', meter_type='smart', install_date=date(2023, 7, 18), is_active=True),
            Meter(id=8, customer_id=8, meter_number='SM-2024-00008', meter_type='digital', install_date=date(2022, 11, 25), is_active=True),
            Meter(id=9, customer_id=9, meter_number='SM-2024-00009', meter_type='smart', install_date=date(2023, 8, 8), is_active=True),
            Meter(id=10, customer_id=10, meter_number='SM-2024-00010', meter_type='smart', install_date=date(2023, 9, 30), is_active=True)
        ]
        db.session.add_all(meters)
        db.session.commit()
        
        # 4. Seed Readings for Customers 1-3
        print("Seeding Readings...")
        readings_c1 = [
            18.52, 19.10, 17.84, 20.31, 16.95, 21.20, 22.88, 19.43, 18.11, 20.76, 17.22, 19.94, 21.55, 18.88
        ]
        readings_c2 = [
            22.10, 21.55, 23.40, 5.20, 3.80, 4.10, 22.90, 21.30, 2.50, 3.10, 23.80, 20.90, 4.60, 2.90
        ]
        readings_c3 = [
            95.20, 12.50, 102.8, 98.1, 110.4, 105.9, 15.30, 88.7, 11.20, 101.5, 107.3, 99.8, 112.1, 13.90
        ]
        
        db_readings = []
        for i, val in enumerate(readings_c1):
            ts = datetime(2024, 6, i+1)
            db_readings.append(MeterReading(meter_id=1, customer_id=1, timestamp=ts, consumption_kwh=val, quality_flag='valid'))
            
        for i, val in enumerate(readings_c2):
            ts = datetime(2024, 6, i+1)
            db_readings.append(MeterReading(meter_id=2, customer_id=2, timestamp=ts, consumption_kwh=val, quality_flag='valid'))
            
        for i, val in enumerate(readings_c3):
            ts = datetime(2024, 6, i+1)
            db_readings.append(MeterReading(meter_id=3, customer_id=3, timestamp=ts, consumption_kwh=val, quality_flag='valid'))
            
        # Seed basic minimal dummy readings for remaining customers 4-10
        for cust_id in range(4, 11):
            for i in range(14):
                ts = datetime(2024, 6, i+1)
                db_readings.append(MeterReading(meter_id=cust_id, customer_id=cust_id, timestamp=ts, consumption_kwh=10.0 + i % 5, quality_flag='valid'))
                
        db.session.add_all(db_readings)
        db.session.commit()
        
        # 5. Seed Predictions
        print("Seeding Predictions...")
        predictions = [
            Prediction(id=1, customer_id=1, bilstm_score=0.082, transformer_score=0.065, fused_score=0.073, risk_score=12, risk_level='low', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=2, customer_id=2, bilstm_score=0.891, transformer_score=0.923, fused_score=0.912, risk_score=91, risk_level='critical', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=3, customer_id=3, bilstm_score=0.120, transformer_score=0.095, fused_score=0.105, risk_score=18, risk_level='low', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=4, customer_id=4, bilstm_score=0.445, transformer_score=0.510, fused_score=0.480, risk_score=52, risk_level='high', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=5, customer_id=5, bilstm_score=0.210, transformer_score=0.180, fused_score=0.195, risk_score=28, risk_level='medium', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=6, customer_id=6, bilstm_score=0.670, transformer_score=0.720, fused_score=0.698, risk_score=72, risk_level='high', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=7, customer_id=7, bilstm_score=0.055, transformer_score=0.042, fused_score=0.048, risk_score=8, risk_level='low', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=8, customer_id=8, bilstm_score=0.780, transformer_score=0.815, fused_score=0.800, risk_score=82, risk_level='critical', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=9, customer_id=9, bilstm_score=0.310, transformer_score=0.280, fused_score=0.295, risk_score=38, risk_level='medium', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0)),
            Prediction(id=10, customer_id=10, bilstm_score=0.150, transformer_score=0.130, fused_score=0.140, risk_score=22, risk_level='low', model_version='v1.0.0', predicted_at=datetime(2024, 6, 15, 10, 0, 0))
        ]
        db.session.add_all(predictions)
        db.session.commit()
        
        # 6. Seed Alerts
        print("Seeding Alerts...")
        alerts = [
            Alert(id=1, customer_id=2, prediction_id=2, severity='critical', status='open', title='Critical Theft Risk Detected', message='Customer CUST-002 shows a fused theft probability of 91.2%. Consumption dropped by 80% on multiple days — strongly indicative of meter tampering.', created_at=datetime(2024, 6, 15, 10, 5, 0)),
            Alert(id=2, customer_id=8, prediction_id=8, severity='critical', status='investigating', title='Critical Theft Risk Detected', message='Customer CUST-008 (suspended account) shows a fused theft probability of 80.0%. Possible unauthorized reconnection.', created_at=datetime(2024, 6, 15, 10, 5, 0)),
            Alert(id=3, customer_id=6, prediction_id=6, severity='high', status='open', title='High Theft Risk Detected', message='Customer CUST-006 shows a fused theft probability of 69.8%. Irregular consumption spikes and drops detected.', created_at=datetime(2024, 6, 15, 10, 5, 0)),
            Alert(id=4, customer_id=4, prediction_id=4, severity='high', status='open', title='High Theft Risk Detected', message='Customer CUST-004 shows a fused theft probability of 48.0%. Moderate anomaly in consumption pattern.', created_at=datetime(2024, 6, 15, 10, 5, 0)),
            Alert(id=5, customer_id=5, prediction_id=5, severity='warning', status='resolved', title='Medium Risk — Consumption Anomaly', message='Customer CUST-005 industrial consumption variance exceeded threshold. Verified as seasonal production shift.', created_at=datetime(2024, 6, 15, 10, 5, 0)),
            Alert(id=6, customer_id=9, prediction_id=9, severity='warning', status='false_positive', title='Medium Risk — Consumption Anomaly', message='Customer CUST-009 flagged due to low consumption during vacation period. Confirmed false positive.', created_at=datetime(2024, 6, 15, 10, 5, 0))
        ]
        db.session.add_all(alerts)
        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
