import os
import random
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.security import generate_password_hash
from models import UserMeterState, db, User, Supplier, Society, ConservationTip, SupplierOffer, Challenge, UserChallenge, TankerOrder, TankerListing, WaterReading
from app import app
import shutil

def get_random_coordinates(base_lat, base_long, radius=0.01):
    """Generate random coordinates within a small radius of a base point."""
    return (
        base_lat + random.uniform(-radius, radius),
        base_long + random.uniform(-radius, radius)
    )

with app.app_context():
    print(">>> Dropping old data...")
    db.drop_all()
    print(">>> Creating tables...")
    db.create_all()

    # 1. Create Society
    print(">>> Creating Society...")
    society = Society(name="Green Valley", address="123 Main St, Mumbai")
    db.session.add(society)
    db.session.commit() # ID = 1

    # 2. Create Users (20 Residents + 1 Admin + 1 Supplier)
    print(">>> Creating Users...")
    users = []
    base_lat, base_long = 19.0760, 72.8777
    
    # Society Admin
    admin = User(username="admin_gv", email="admin@greenvalley.com", role="society_admin", society_id=1, area="Andheri", city="Mumbai", lat=base_lat, long=base_long)
    admin.set_password("admin123")
    users.append(admin)

    # Supplier User (External)
    supplier_user = User(username="water_king", email="orders@waterking.com", role="supplier")
    supplier_user.set_password("supplier123")
    users.append(supplier_user)

    # Tanker Owner User
    tanker_owner = User(
        username="owner_raj",
        email="owner@aquafleet.com",
        role="tanker_owner",
        area="Andheri",
        city="Mumbai",
        lat=base_lat,
        long=base_long,
    )
    tanker_owner.set_password("owner123")
    users.append(tanker_owner)

    # 20 Residents
    first_names = ["John","Aarav", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Diya", "Saanvi", "Ananya", "Aadhya", "Pari", "Saanvi", "Myra", "Riya", "Aarohi", "Anika"]
    
    for i, name in enumerate(first_names):
        lat, long = get_random_coordinates(base_lat, base_long)
        user = User(
            username=f"{name.lower()}_{i+1}",
            email=f"{name.lower()}{i+1}@example.com",
            role="user",
            society_id=1,
            area="Andheri",
            city="Mumbai",
            lat=lat,
            long=long
        )
        user.set_password("pass123")
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    # Get user IDs for later use (exclude admin/supplier from random user lists if needed, but here we assume residents are ID 3 to 22)
    resident_ids = [u.id for u in users if u.role == 'user']

    # ---------------------------------------------------------
    # 3. Create Suppliers & Offers
    # ---------------------------------------------------------
    print(">>> Creating Suppliers & Offers...")
    suppliers = [
        Supplier(name="Mumbai Jal Board", contact="+91-22-12345678", verified=True, photo_url="https://cdn.dnaindia.com/sites/default/files/2018/04/16/672411-water-tanker-05.jpg?im=FitAndFill=(300,225)", area="Mumbai", city="Mumbai", rating=3.8, num_reviews=50, lat=19.08, long=72.88),
        Supplier(name="AquaQuick Tankers", contact="+91-9876543210", verified=True, photo_url="https://www.hindustantimes.com/ht-img/img/2023/04/04/550x309/Mumbai--India---April-04--2023--A-water-tanker-sup_1680635692044.jpg", area="Andheri", city="Mumbai", rating=4.6, num_reviews=25, lat=19.11, long=72.85),
        Supplier(name="PureDrops Pvt Ltd", contact="+91-9988776655", verified=True, photo_url="https://www.hindustantimes.com/ht-img/img/2023/05/08/550x309/Due-to-higher-water-demands--the-number-of-water-t_1683567413698.jpg", area="Juhu", city="Mumbai", rating=4.2, num_reviews=15, lat=19.09, long=72.83),
        Supplier(name="Crystal Clear Water", contact="+91-8877665544", verified=True, photo_url="https://indianexpress.com/wp-content/uploads/2019/08/strike-feature.jpg", area="Bandra", city="Mumbai", rating=4.8, num_reviews=40, lat=19.05, long=72.84),
        Supplier(name="EcoWater Transport", contact="+91-7766554433", verified=False, photo_url="https://5.imimg.com/data5/SELLER/Default/2023/4/297592358/HE/CC/UD/24635301/whatsapp-image-2023-04-03-at-10-12-54-am-1000x1000.jpeg", area="Vile Parle", city="Mumbai", rating=3.5, num_reviews=8, lat=19.10, long=72.86),
    ]
    db.session.add_all(suppliers)
    db.session.commit()

    # ---------------------------------------------------------
    # 3B. Create Tanker Owner Listings
    # ---------------------------------------------------------
    print(">>> Creating Tanker Listings...")
    owner = User.query.filter_by(username="owner_raj").first()
    if owner:
        tankers = [
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-AB-4455",
                tanker_type="Standard",
                capacity=5000.0,
                price_per_liter=0.45,
                base_delivery_fee=300.0,
                service_areas='["Andheri", "Juhu", "Vile Parle"]',
                images='["https://images.unsplash.com/photo-1572675339312-3e8b094a5440?auto=format&fit=crop&w=900&q=80"]',
                amenities='["GPS Tracking", "Water Quality Certificate"]',
                description="Reliable 5KL tanker for same-day deliveries.",
                emergency_contact="+91-9000011111",
                status="available",
                area="Andheri",
                city="Mumbai",
                lat=19.115,
                long=72.846,
            ),
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-CD-7788",
                tanker_type="Premium",
                capacity=10000.0,
                price_per_liter=0.60,
                base_delivery_fee=450.0,
                service_areas='["Bandra", "Andheri", "Santacruz"]',
                images='["https://images.unsplash.com/photo-1509395176047-4a66953fd231?auto=format&fit=crop&w=900&q=80"]',
                amenities='["24x7 Support", "Fast Dispatch"]',
                description="Premium 10KL tanker for bulk and emergency demand.",
                emergency_contact="+91-9000022222",
                status="available",
                area="Bandra",
                city="Mumbai",
                lat=19.061,
                long=72.834,
            ),

            # Dummy listings mapped from old Supplier-style coverage
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-EF-1122",
                tanker_type="Standard",
                capacity=6000.0,
                price_per_liter=0.48,
                base_delivery_fee=320.0,
                service_areas='["Mumbai", "Byculla", "Dadar"]',
                images='["https://cdn.dnaindia.com/sites/default/files/2018/04/16/672411-water-tanker-05.jpg?im=FitAndFill=(300,225)"]',
                amenities='["Verified Quality", "City Permit"]',
                description="City coverage tanker for central Mumbai.",
                emergency_contact="+91-9000033333",
                status="available",
                area="Mumbai",
                city="Mumbai",
                lat=19.080,
                long=72.880,
            ),
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-GH-3344",
                tanker_type="Express",
                capacity=7000.0,
                price_per_liter=0.52,
                base_delivery_fee=350.0,
                service_areas='["Andheri", "Jogeshwari", "Goregaon"]',
                images='["https://www.hindustantimes.com/ht-img/img/2023/04/04/550x309/Mumbai--India---April-04--2023--A-water-tanker-sup_1680635692044.jpg"]',
                amenities='["Fast Dispatch", "GPS Tracking"]',
                description="Fast dispatch tanker for west suburbs.",
                emergency_contact="+91-9000044444",
                status="available",
                area="Andheri",
                city="Mumbai",
                lat=19.110,
                long=72.850,
            ),
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-IJ-5566",
                tanker_type="Standard",
                capacity=8000.0,
                price_per_liter=0.50,
                base_delivery_fee=360.0,
                service_areas='["Juhu", "Santacruz", "Vile Parle"]',
                images='["https://www.hindustantimes.com/ht-img/img/2023/05/08/550x309/Due-to-higher-water-demands--the-number-of-water-t_1683567413698.jpg"]',
                amenities='["Water Quality Certificate"]',
                description="Balanced cost tanker for Juhu belt.",
                emergency_contact="+91-9000055555",
                status="available",
                area="Juhu",
                city="Mumbai",
                lat=19.090,
                long=72.830,
            ),
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-KL-7789",
                tanker_type="Premium",
                capacity=9000.0,
                price_per_liter=0.58,
                base_delivery_fee=420.0,
                service_areas='["Bandra", "Khar", "Santacruz"]',
                images='["https://indianexpress.com/wp-content/uploads/2019/08/strike-feature.jpg"]',
                amenities='["24x7 Support", "Priority Delivery"]',
                description="Premium tanker for Bandra and nearby zones.",
                emergency_contact="+91-9000066666",
                status="available",
                area="Bandra",
                city="Mumbai",
                lat=19.050,
                long=72.840,
            ),
            TankerListing(
                owner_id=owner.id,
                vehicle_number="MH-01-MN-9900",
                tanker_type="Economy",
                capacity=5000.0,
                price_per_liter=0.43,
                base_delivery_fee=280.0,
                service_areas='["Vile Parle", "Andheri East", "Kurla"]',
                images='["https://5.imimg.com/data5/SELLER/Default/2023/4/297592358/HE/CC/UD/24635301/whatsapp-image-2023-04-03-at-10-12-54-am-1000x1000.jpeg"]',
                amenities='["Affordable Plan"]',
                description="Economy tanker option for daily needs.",
                emergency_contact="+91-9000077777",
                status="available",
                area="Vile Parle",
                city="Mumbai",
                lat=19.100,
                long=72.860,
            ),
        ]
        db.session.add_all(tankers)
        db.session.commit()

    # Create diverse offers
    offers = []
    # Mix of small (1k-2k), medium (5k-8k), and large (10k-15k) tankers with varying prices
    for sup_id in range(1, 6):
        # Small
        offers.append(SupplierOffer(supplier_id=sup_id, quantity=1000.0, cost=random.randint(400, 600)))
        offers.append(SupplierOffer(supplier_id=sup_id, quantity=2000.0, cost=random.randint(800, 1100)))
        # Medium
        offers.append(SupplierOffer(supplier_id=sup_id, quantity=5000.0, cost=random.randint(1800, 2200)))
        # Large (Only some suppliers)
        if sup_id % 2 != 0: 
            offers.append(SupplierOffer(supplier_id=sup_id, quantity=10000.0, cost=random.randint(3500, 4200)))
            offers.append(SupplierOffer(supplier_id=sup_id, quantity=15000.0, cost=random.randint(5000, 6000)))

    db.session.add_all(offers)
    db.session.commit()

    # ---------------------------------------------------------
    # 4. Challenges & Conservation Tips
    # ---------------------------------------------------------
    print(">>> Creating Content...")
    tips = [
        ConservationTip(title="RO Waste Reuse", content="Collect RO purifier waste water to mop floors.", location_specific="urban_india"),
        ConservationTip(title="Rice Water for Plants", content="Use water from washing rice/dal for watering plants.", location_specific="urban_india"),
        ConservationTip(title="Aerators", content="Install aerators on taps to reduce flow by 50%.", location_specific="urban_india"),
        ConservationTip(title="Leak Check", content="Check toilet flushes for silent leaks using food coloring.", location_specific="global"),
    ]
    db.session.add_all(tips)

    challenges = [
        Challenge(name="Leak Detective", short_desc="Find and fix 1 leak", full_desc="Inspect all taps and fix one dripping faucet.", water_save_potential=30.0, eco_points=50),
        Challenge(name="5-Min Shower", short_desc="Limit showers to 5 mins", full_desc="Use a timer to ensure showers don't exceed 5 minutes.", water_save_potential=100.0, eco_points=20),
        Challenge(name="Bucket Challenge", short_desc="Bath with 1 bucket only", full_desc="Use only one bucket for bathing for a week.", water_save_potential=150.0, eco_points=40),
        Challenge(name="Full Load Laundry", short_desc="Only run full loads", full_desc="Wait until you have a full load before running the washing machine.", water_save_potential=80.0, eco_points=30),
    ]
    db.session.add_all(challenges)
    db.session.commit()

    # ---------------------------------------------------------
    # 5. Generate User Activity (Challenges)
    # ---------------------------------------------------------
    print(">>> Generating User Activity...")
    user_challenges = []
    statuses = ['active', 'completed', 'pending', 'failed']
    
    for uid in resident_ids:
        # Assign 2-3 random challenges to each user
        chosen_challenges = random.sample(range(1, 5), k=random.randint(2, 3))
        for cid in chosen_challenges:
            status = random.choice(statuses)
            saved = 0.0
            points = 0
            if status == 'completed':
                saved = random.uniform(50, 200)
                points = random.randint(10, 50)
            
            uc = UserChallenge(
                user_id=uid,
                challenge_id=cid,
                progress=100.0 if status == 'completed' else random.uniform(0, 80),
                status=status,
                start_date=datetime.utcnow() - timedelta(days=random.randint(5, 20)),
                end_date=datetime.utcnow() if status == 'completed' else None,
                water_saved=saved,
                eco_points_earned=points
            )
            user_challenges.append(uc)
    db.session.add_all(user_challenges)
    db.session.commit()

    society_id = 1
    resident_ids = [u.id for u in User.query.filter_by(role='user').all()]

    # ---------------------------------------------------------
    # Generate Massive Water Reading Data -> PARQUET FILES
    # ---------------------------------------------------------
    print(">>> Generating IoT Water Readings (Parquet)...")
    
    base_dir = "/app/data/raw/water_readings"
    # Nuke the old data lake folder if it exists
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    
    now = datetime.utcnow()
    # Baseline meter readings (e.g., installed 120 days ago)
    current_meter_value = {uid: random.uniform(1000, 5000) for uid in resident_ids}
    
    # We will simulate writing daily parquet files
    for day in range(120, -1, -1):
        target_date = (now - timedelta(days=day)).date()
        daily_records = []
        db_readings = []
        
        # 3 readings a day per user
        for hour in [7, 14, 21]:
            for uid in resident_ids:
                if hour == 7: usage = random.uniform(100, 200)
                elif hour == 14: usage = random.uniform(20, 50)
                else: usage = random.uniform(50, 100)
                
                if random.random() > 0.9: usage += 150 # Spike
                
                current_meter_value[uid] += usage
                
                daily_records.append({
                    "user_id": uid,
                    "society_id": society_id,
                    "timestamp": datetime.combine(target_date, datetime.min.time()).replace(hour=hour),
                    "reading": current_meter_value[uid]
                })

                db_readings.append(WaterReading(
                    user_id=uid,
                    reading=current_meter_value[uid],
                    society_id=society_id,
                    timestamp=datetime.combine(target_date, datetime.min.time()).replace(hour=hour)
                ))
        
        # Write to Parquet Partition
        df = pd.DataFrame(daily_records)
        df['timestamp'] = df['timestamp'].astype('datetime64[us]')
        partition_dir = os.path.join(base_dir, f"date={target_date}")
        os.makedirs(partition_dir, exist_ok=True)
        df.to_parquet(
            os.path.join(partition_dir, "data.parquet"), 
            engine='pyarrow', 
            use_deprecated_int96_timestamps=True
        )

        # Keep legacy consumption endpoints working by storing readings in DB too.
        db.session.add_all(db_readings)

    # ---------------------------------------------------------
    # Initialize State Table for Spark
    # ---------------------------------------------------------
    print(">>> Saving Initial Meter States...")
    states = []
    for uid in resident_ids:
        states.append(UserMeterState(
            user_id=uid,
            last_reading=current_meter_value[uid],
            last_updated=now.date()
        ))
    db.session.add_all(states)
    db.session.commit()
    print(">>> Database & Data Lake populated successfully!")

    # ---------------------------------------------------------
    # 7. Generate Tanker Orders
    # ---------------------------------------------------------
    print(">>> Generating Tanker Orders...")
    orders = []
    order_statuses = ['pending', 'en_route', 'delivered', 'cancelled']
    
    # Generate ~30 orders over the last 3 months
    for _ in range(30):
        # Random Resident or Admin placing order
        buyer_id = random.choice([1] + resident_ids) # 1 is admin
        supplier_id = random.randint(1, 5)
        days_ago = random.randint(0, 90)
        status = 'delivered' if days_ago > 2 else random.choice(['pending', 'en_route'])
        
        o_date = now - timedelta(days=days_ago)
        
        orders.append(TankerOrder(
            user_id=buyer_id,
            supplier_id=supplier_id,
            society_id=1,
            volume=random.choice([5000.0, 10000.0, 12000.0]),
            price=random.uniform(2000, 5000),
            status=status,
            order_time=o_date,
            delivery_time=o_date + timedelta(hours=random.randint(2, 6))
        ))
    db.session.add_all(orders)

    db.session.commit()
    print(">>> Database populated successfully with rich data!")