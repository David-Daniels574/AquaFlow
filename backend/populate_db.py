import os
import random
import shutil
from datetime import datetime, timedelta
from urllib.parse import unquote, urlparse

import pandas as pd
import psycopg2
import redis
from psycopg2 import sql
from sqlalchemy import text

from auth_service.app import app as auth_app
from auth_service.models import Society, User, db as auth_db
from booking_service.app import app as booking_app
from booking_service.models import TankerBooking, TankerOrder, db as booking_db
from gamification_service.app import app as gamification_app
from gamification_service.models import (
    Broadcast,
    Challenge,
    ConservationTip,
    DiscussionThread,
    ThreadComment,
    UserChallenge,
    db as gamification_db,
)
from iot_analytics_service.app import app as iot_app
from iot_analytics_service.models import UserDailyUsage, UserMeterState, WaterReading, db as iot_db
from supplier_service.app import app as supplier_app
from supplier_service.models import Supplier, SupplierOffer, TankerListing, db as supplier_db


SEED_RANDOM_VALUE = 42


def _parse_postgres_url(db_url):
    parsed = urlparse(db_url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "dbname": (parsed.path or "/").lstrip("/"),
    }


def ensure_service_databases():
    db_env_vars = [
        "AUTH_DATABASE_URL",
        "SUPPLIER_DATABASE_URL",
        "BOOKING_DATABASE_URL",
        "GAMIFICATION_DATABASE_URL",
        "IOT_DATABASE_URL",
    ]

    db_urls = []
    for env_var in db_env_vars:
        db_url = os.environ.get(env_var, "").strip()
        if db_url.startswith("postgresql://"):
            db_urls.append((env_var, db_url))

    if not db_urls:
        print("No PostgreSQL service URLs found. Skipping DB existence check.")
        return

    parsed_urls = [(env_var, _parse_postgres_url(db_url)) for env_var, db_url in db_urls]
    first = parsed_urls[0][1]
    admin_candidates = []
    for candidate in ("postgres", "appdb", first["dbname"]):
        if candidate and candidate not in admin_candidates:
            admin_candidates.append(candidate)

    admin_conn = None
    for admin_db in admin_candidates:
        try:
            admin_conn = psycopg2.connect(
                host=first["host"],
                port=first["port"],
                user=first["user"],
                password=first["password"],
                dbname=admin_db,
            )
            print(f"Connected to admin database '{admin_db}' to verify service databases.")
            break
        except psycopg2.OperationalError as exc:
            print(f"Failed to connect to admin database '{admin_db}': {exc}")

    if not admin_conn:
        raise RuntimeError("Could not connect to PostgreSQL admin database to verify service DBs.")

    try:
        admin_conn.autocommit = True
        with admin_conn.cursor() as cur:
            for env_var, parsed in parsed_urls:
                db_name = parsed["dbname"]
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                if cur.fetchone():
                    print(f"Database '{db_name}' already exists ({env_var}).")
                    continue

                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"Created missing database '{db_name}' ({env_var}).")
    finally:
        admin_conn.close()


def reset_service_database(app, service_db, service_name):
    with app.app_context():
        print(f"Resetting {service_name} database...")
        service_db.session.remove()
        service_db.engine.dispose()

        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("postgresql://"):
            with service_db.engine.begin() as conn:
                conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
                conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

        service_db.drop_all()
        service_db.create_all()


def clear_redis_cache():
    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    try:
        redis_client = redis.Redis.from_url(redis_url)
        redis_client.flushdb()
        print(f"Cleared Redis cache at {redis_url}")
    except redis.RedisError as exc:
        print(f"Warning: failed to clear Redis cache at {redis_url}: {exc}")


def get_random_coordinates(base_lat, base_long, radius=0.01):
    return base_lat + random.uniform(-radius, radius), base_long + random.uniform(-radius, radius)


def seed_auth_service():
    with auth_app.app_context():
        print("Seeding auth_service...")

        society = Society(name="Green Valley", address="123 Main St, Mumbai")
        auth_db.session.add(society)
        auth_db.session.commit()

        users = []
        base_lat, base_long = 19.0760, 72.8777
        admin = User(
            username="admin_gv",
            email="admin@greenvalley.com",
            role="society_admin",
            society_id=society.id,
            area="Andheri",
            city="Mumbai",
            lat=base_lat,
            long=base_long,
        )
        admin.set_password("admin123")
        users.append(admin)

        supplier_user = User(username="water_king", email="orders@waterking.com", role="supplier")
        supplier_user.set_password("supplier123")
        users.append(supplier_user)

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

        first_names = [
            "John",
            "Aarav",
            "Aditya",
            "Vihaan",
            "Arjun",
            "Sai",
            "Reyansh",
            "Ayaan",
            "Krishna",
            "Ishaan",
            "Diya",
            "Saanvi",
            "Ananya",
            "Aadhya",
            "Pari",
            "Myra",
            "Riya",
            "Aarohi",
            "Anika",
            "Kabir",
        ]
        for index, name in enumerate(first_names):
            lat, long = get_random_coordinates(base_lat, base_long)
            user = User(
                username=f"{name.lower()}_{index + 1}",
                email=f"{name.lower()}{index + 1}@example.com",
                role="user",
                society_id=society.id,
                area="Andheri",
                city="Mumbai",
                lat=lat,
                long=long,
            )
            user.set_password("pass123")
            users.append(user)

        auth_db.session.add_all(users)
        auth_db.session.commit()

        residents = User.query.filter_by(role="user").all()
        return {
            "society_id": society.id,
            "admin_id": admin.id,
            "supplier_user_id": supplier_user.id,
            "owner_id": tanker_owner.id,
            "resident_ids": [resident.id for resident in residents],
        }


def seed_supplier_service(owner_id):
    with supplier_app.app_context():
        print("Seeding supplier_service...")

        suppliers = [
            Supplier(
                name="Mumbai Jal Board",
                contact="+91-22-12345678",
                verified=True,
                photo_url="https://cdn.dnaindia.com/sites/default/files/2018/04/16/672411-water-tanker-05.jpg",
                area="Mumbai",
                city="Mumbai",
                rating=3.8,
                num_reviews=50,
                lat=19.08,
                long=72.88,
            ),
            Supplier(
                name="AquaQuick Tankers",
                contact="+91-9876543210",
                verified=True,
                photo_url="https://www.hindustantimes.com/ht-img/img/2023/04/04/550x309/Mumbai--India.jpg",
                area="Andheri",
                city="Mumbai",
                rating=4.6,
                num_reviews=25,
                lat=19.11,
                long=72.85,
            ),
            Supplier(
                name="Crystal Clear Water",
                contact="+91-8877665544",
                verified=True,
                photo_url="https://indianexpress.com/wp-content/uploads/2019/08/strike-feature.jpg",
                area="Bandra",
                city="Mumbai",
                rating=4.8,
                num_reviews=40,
                lat=19.05,
                long=72.84,
            ),
            Supplier(
                name="BlueDrop Logistics",
                contact="+91-9988776655",
                verified=True,
                photo_url="https://images.unsplash.com/photo-1520607162513-77705c0f0d4a",
                area="Powai",
                city="Mumbai",
                rating=4.4,
                num_reviews=31,
                lat=19.119,
                long=72.905,
            ),
            Supplier(
                name="HydroFast Deliveries",
                contact="+91-9123456780",
                verified=True,
                photo_url="https://images.unsplash.com/photo-1494412651409-8963ce7935a7",
                area="Goregaon",
                city="Mumbai",
                rating=4.2,
                num_reviews=18,
                lat=19.164,
                long=72.849,
            ),
            Supplier(
                name="SafeWater Fleet",
                contact="+91-9234567812",
                verified=True,
                photo_url="https://images.unsplash.com/photo-1469474968028-56623f02e42e",
                area="Chembur",
                city="Mumbai",
                rating=4.5,
                num_reviews=27,
                lat=19.052,
                long=72.893,
            ),
            Supplier(
                name="Metro Aqua Supply",
                contact="+91-9345678123",
                verified=True,
                photo_url="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
                area="Dadar",
                city="Mumbai",
                rating=4.3,
                num_reviews=22,
                lat=19.018,
                long=72.842,
            ),
            Supplier(
                name="CityTank WaterWorks",
                contact="+91-9456781234",
                verified=True,
                photo_url="https://images.unsplash.com/photo-1450101499163-c8848c66ca85",
                area="Kurla",
                city="Mumbai",
                rating=4.1,
                num_reviews=15,
                lat=19.072,
                long=72.882,
            ),
        ]
        supplier_db.session.add_all(suppliers)
        supplier_db.session.commit()

        offers = []
        for supplier in suppliers:
            offers.append(SupplierOffer(supplier_id=supplier.id, quantity=1000.0, cost=random.randint(400, 600)))
            offers.append(SupplierOffer(supplier_id=supplier.id, quantity=5000.0, cost=random.randint(1800, 2200)))
            offers.append(SupplierOffer(supplier_id=supplier.id, quantity=10000.0, cost=random.randint(3500, 4200)))
        supplier_db.session.add_all(offers)

        tankers = [
            TankerListing(
                owner_id=owner_id,
                vehicle_number="MH-01-AB-4455",
                tanker_type="Standard",
                capacity=5000.0,
                price_per_liter=0.45,
                base_delivery_fee=300.0,
                service_areas='["Andheri", "Juhu", "Vile Parle"]',
                images='["https://images.unsplash.com/photo-1572675339312-3e8b094a5440"]',
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
                owner_id=owner_id,
                vehicle_number="MH-01-CD-7788",
                tanker_type="Premium",
                capacity=10000.0,
                price_per_liter=0.60,
                base_delivery_fee=450.0,
                service_areas='["Bandra", "Andheri", "Santacruz"]',
                images='["https://images.unsplash.com/photo-1509395176047-4a66953fd231"]',
                amenities='["24x7 Support", "Fast Dispatch"]',
                description="Premium 10KL tanker for bulk and emergency demand.",
                emergency_contact="+91-9000022222",
                status="available",
                area="Bandra",
                city="Mumbai",
                lat=19.061,
                long=72.834,
            ),
            TankerListing(
                owner_id=owner_id,
                vehicle_number="MH-01-EF-9921",
                tanker_type="Standard",
                capacity=3000.0,
                price_per_liter=0.40,
                base_delivery_fee=220.0,
                service_areas='["Powai", "Vikhroli", "Ghatkopar"]',
                images='["https://images.unsplash.com/photo-1473448912268-2022ce9509d8"]',
                amenities='["Fast Dispatch", "Digital Invoicing"]',
                description="Compact tanker for quick urban deliveries.",
                emergency_contact="+91-9000033333",
                status="available",
                area="Powai",
                city="Mumbai",
                lat=19.118,
                long=72.907,
            ),
            TankerListing(
                owner_id=owner_id,
                vehicle_number="MH-01-GH-2201",
                tanker_type="Industrial",
                capacity=12000.0,
                price_per_liter=0.66,
                base_delivery_fee=520.0,
                service_areas='["Chembur", "Kurla", "Sion"]',
                images='["https://images.unsplash.com/photo-1465447142348-e9952c393450"]',
                amenities='["GPS Tracking", "High Pressure Pump"]',
                description="Industrial-grade tanker for high-capacity demand.",
                emergency_contact="+91-9000044444",
                status="available",
                area="Chembur",
                city="Mumbai",
                lat=19.051,
                long=72.892,
            ),
            TankerListing(
                owner_id=owner_id,
                vehicle_number="MH-01-IJ-7754",
                tanker_type="Premium",
                capacity=8000.0,
                price_per_liter=0.58,
                base_delivery_fee=390.0,
                service_areas='["Dadar", "Matunga", "Mahim"]',
                images='["https://images.unsplash.com/photo-1451187580459-43490279c0fa"]',
                amenities='["24x7 Support", "Certified Driver"]',
                description="Premium tanker suited for frequent society orders.",
                emergency_contact="+91-9000055555",
                status="busy",
                area="Dadar",
                city="Mumbai",
                lat=19.019,
                long=72.841,
            ),
            TankerListing(
                owner_id=owner_id,
                vehicle_number="MH-01-KL-1189",
                tanker_type="Standard",
                capacity=6000.0,
                price_per_liter=0.49,
                base_delivery_fee=310.0,
                service_areas='["Andheri", "Goregaon", "Jogeshwari"]',
                images='["https://images.unsplash.com/photo-1509395176047-4a66953fd231"]',
                amenities='["Water Quality Certificate"]',
                description="Balanced option for daily apartment deliveries.",
                emergency_contact="+91-9000066666",
                status="available",
                area="Goregaon",
                city="Mumbai",
                lat=19.163,
                long=72.848,
            ),
            TankerListing(
                owner_id=owner_id,
                vehicle_number="MH-01-MN-4502",
                tanker_type="Standard",
                capacity=4500.0,
                price_per_liter=0.43,
                base_delivery_fee=250.0,
                service_areas='["Bandra", "Santacruz", "Khar"]',
                images='["https://images.unsplash.com/photo-1520607162513-77705c0f0d4a"]',
                amenities='["GPS Tracking"]',
                description="Mid-size tanker for west-line rapid drops.",
                emergency_contact="+91-9000077777",
                status="available",
                area="Bandra",
                city="Mumbai",
                lat=19.060,
                long=72.833,
            ),
        ]
        supplier_db.session.add_all(tankers)
        supplier_db.session.commit()
        print(f"Seeded {len(suppliers)} suppliers, {len(offers)} offers, {len(tankers)} tankers")
        return {"supplier_ids": [supplier.id for supplier in suppliers], "tanker_ids": [tanker.id for tanker in tankers]}


def seed_booking_service(seed_data, supplier_ids, tanker_ids):
    with booking_app.app_context():
        print("Seeding booking_service...")

        orders = []
        now = datetime.utcnow()
        for _ in range(20):
            days_ago = random.randint(0, 90)
            order_date = now - timedelta(days=days_ago)
            status = "delivered" if days_ago > 2 else random.choice(["pending", "en_route"])
            orders.append(
                TankerOrder(
                    user_id=random.choice(seed_data["resident_ids"]),
                    supplier_id=random.choice(supplier_ids),
                    society_id=seed_data["society_id"],
                    volume=random.choice([5000.0, 10000.0, 12000.0]),
                    price=round(random.uniform(2000, 5000), 2),
                    status=status,
                    order_time=order_date,
                    delivery_time=order_date + timedelta(hours=random.randint(2, 6)),
                )
            )
        booking_db.session.add_all(orders)

        bookings = []
        for index in range(10):
            status = random.choice(["pending", "confirmed", "in_transit", "completed"])
            bookings.append(
                TankerBooking(
                    tanker_id=random.choice(tanker_ids),
                    owner_id=seed_data["owner_id"],
                    tanker_vehicle_number=f"MH-01-RND-{1000 + index}",
                    customer_id=random.choice(seed_data["resident_ids"]),
                    delivery_address="Green Valley Society",
                    delivery_pincode="400001",
                    quantity=random.choice([2000.0, 3000.0, 5000.0]),
                    total_amount=round(random.uniform(1200, 3800), 2),
                    status=status,
                    scheduled_time=now + timedelta(days=random.randint(1, 7)),
                    delivered_time=now - timedelta(days=1) if status == "completed" else None,
                )
            )
        booking_db.session.add_all(bookings)
        booking_db.session.commit()


def seed_gamification_service(seed_data):
    with gamification_app.app_context():
        print("Seeding gamification_service...")

        tips = [
            ConservationTip(title="RO Waste Reuse", content="Collect RO purifier waste water to mop floors.", location_specific="urban_india"),
            ConservationTip(title="Rice Water for Plants", content="Use water from washing rice/dal for watering plants.", location_specific="urban_india"),
            ConservationTip(title="Leak Check", content="Check toilet flushes for silent leaks using food coloring.", location_specific="global"),
        ]
        gamification_db.session.add_all(tips)

        challenges = [
            Challenge(name="Leak Detective", short_desc="Find and fix 1 leak", full_desc="Inspect all taps and fix one dripping faucet.", water_save_potential=30.0, eco_points=50),
            Challenge(name="5-Min Shower", short_desc="Limit showers to 5 mins", full_desc="Use a timer to ensure showers do not exceed 5 minutes.", water_save_potential=100.0, eco_points=20),
            Challenge(name="Bucket Challenge", short_desc="Bath with 1 bucket only", full_desc="Use only one bucket for bathing for a week.", water_save_potential=150.0, eco_points=40),
        ]
        gamification_db.session.add_all(challenges)
        gamification_db.session.commit()

        user_challenges = []
        for user_id in seed_data["resident_ids"]:
            selected = random.sample(challenges, k=min(2, len(challenges)))
            for challenge in selected:
                status = random.choice(["active", "completed", "pending"])
                progress = 100.0 if status == "completed" else random.uniform(10, 80)
                user_challenges.append(
                    UserChallenge(
                        user_id=user_id,
                        challenge_id=challenge.id,
                        progress=progress,
                        status=status,
                        start_date=datetime.utcnow() - timedelta(days=random.randint(3, 20)),
                        end_date=datetime.utcnow() if status == "completed" else None,
                        water_saved=challenge.water_save_potential if status == "completed" else 0.0,
                        eco_points_earned=challenge.eco_points if status == "completed" else 0,
                    )
                )
        gamification_db.session.add_all(user_challenges)

        broadcast = Broadcast(
            society_id=seed_data["society_id"],
            title="Water Shutdown Notice",
            content="Maintenance work scheduled on Sunday from 9 AM to 12 PM.",
        )
        gamification_db.session.add(broadcast)

        thread = DiscussionThread(
            society_id=seed_data["society_id"],
            user_id=seed_data["resident_ids"][0],
            title="Rainwater Harvesting Ideas",
            content="Can we organize a society-wide workshop?",
            category="Suggestion",
        )
        gamification_db.session.add(thread)
        gamification_db.session.commit()

        comment = ThreadComment(
            thread_id=thread.id,
            user_id=seed_data["resident_ids"][1],
            content="Great idea, we should do it next weekend.",
        )
        gamification_db.session.add(comment)
        gamification_db.session.commit()


def seed_iot_service(seed_data):
    with iot_app.app_context():
        print("Seeding iot_analytics_service...")

        now = datetime.utcnow()
        readings = []
        daily_usage_rows = []
        meter_states = []
        parquet_records = []

        for user_id in seed_data["resident_ids"]:
            meter_value = random.uniform(1000, 5000)
            for day in range(30, -1, -1):
                target_date = (now - timedelta(days=day)).date()
                day_start = meter_value
                for hour in [7, 14, 21]:
                    usage = random.uniform(20, 200)
                    meter_value += usage
                    timestamp = datetime.combine(target_date, datetime.min.time()).replace(hour=hour)
                    readings.append(
                        WaterReading(
                            user_id=user_id,
                            society_id=seed_data["society_id"],
                            reading=meter_value,
                            timestamp=timestamp,
                        )
                    )
                    parquet_records.append(
                        {
                            "user_id": user_id,
                            "society_id": seed_data["society_id"],
                            "date": target_date.isoformat(),
                            "timestamp": timestamp,
                            "reading": meter_value,
                        }
                    )
                daily_usage_rows.append(
                    UserDailyUsage(
                        user_id=user_id,
                        society_id=seed_data["society_id"],
                        date=target_date,
                        total_usage_liters=round(max(meter_value - day_start, 0), 2),
                    )
                )
            meter_states.append(UserMeterState(user_id=user_id, last_reading=meter_value, last_updated=now.date()))

        iot_db.session.add_all(readings)
        iot_db.session.add_all(daily_usage_rows)
        iot_db.session.add_all(meter_states)
        iot_db.session.commit()

        data_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "water_readings"))
        if os.path.exists(data_root):
            shutil.rmtree(data_root)
        os.makedirs(data_root, exist_ok=True)

        df = pd.DataFrame(parquet_records)
        # Spark 3.5 cannot parse TIMESTAMP(NANOS,false) written by default in some pyarrow paths.
        # Force microsecond precision for parquet compatibility.
        df["timestamp"] = pd.to_datetime(df["timestamp"]).astype("datetime64[us]")
        for date_key, group in df.groupby("date"):
            partition_dir = os.path.join(data_root, f"date={date_key}")
            os.makedirs(partition_dir, exist_ok=True)
            group.drop(columns=["date"]).to_parquet(
                os.path.join(partition_dir, "data.parquet"),
                engine="pyarrow",
                index=False,
                coerce_timestamps="us",
                allow_truncated_timestamps=True,
                use_deprecated_int96_timestamps=True,
            )


if __name__ == "__main__":
    random.seed(SEED_RANDOM_VALUE)
    ensure_service_databases()
    clear_redis_cache()

    reset_service_database(auth_app, auth_db, "auth_service")
    reset_service_database(supplier_app, supplier_db, "supplier_service")
    reset_service_database(booking_app, booking_db, "booking_service")
    reset_service_database(gamification_app, gamification_db, "gamification_service")
    reset_service_database(iot_app, iot_db, "iot_analytics_service")

    seed_info = seed_auth_service()
    supplier_seed = seed_supplier_service(seed_info["owner_id"])
    seed_booking_service(seed_info, supplier_seed["supplier_ids"], supplier_seed["tanker_ids"])
    seed_gamification_service(seed_info)
    seed_iot_service(seed_info)
    print("All microservice databases seeded successfully.")
