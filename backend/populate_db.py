import os
import random
import shutil
from datetime import datetime, timedelta

import pandas as pd

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


def get_random_coordinates(base_lat, base_long, radius=0.01):
    return base_lat + random.uniform(-radius, radius), base_long + random.uniform(-radius, radius)


def seed_auth_service():
    with auth_app.app_context():
        print("Seeding auth_service...")
        auth_db.drop_all()
        auth_db.create_all()

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
        supplier_db.drop_all()
        supplier_db.create_all()

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
        ]
        supplier_db.session.add_all(tankers)
        supplier_db.session.commit()
        return {"supplier_ids": [supplier.id for supplier in suppliers], "tanker_ids": [tanker.id for tanker in tankers]}


def seed_booking_service(seed_data, supplier_ids, tanker_ids):
    with booking_app.app_context():
        print("Seeding booking_service...")
        booking_db.drop_all()
        booking_db.create_all()

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
        gamification_db.drop_all()
        gamification_db.create_all()

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
        iot_db.drop_all()
        iot_db.create_all()

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
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for date_key, group in df.groupby("date"):
            partition_dir = os.path.join(data_root, f"date={date_key}")
            os.makedirs(partition_dir, exist_ok=True)
            group.drop(columns=["date"]).to_parquet(
                os.path.join(partition_dir, "data.parquet"),
                engine="pyarrow",
                index=False,
            )


if __name__ == "__main__":
    seed_info = seed_auth_service()
    supplier_seed = seed_supplier_service(seed_info["owner_id"])
    seed_booking_service(seed_info, supplier_seed["supplier_ids"], supplier_seed["tanker_ids"])
    seed_gamification_service(seed_info)
    seed_iot_service(seed_info)
    print("All microservice databases seeded successfully.")
