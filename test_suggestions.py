#!/usr/bin/env python
"""
Test script for Seat Suggestions Generator
1. Creates mock data (rooms, seats, users, bookings, temperature readings, energy states)
2. Logs in a user and obtains a JWT token
3. Calls POST /seat-suggestions/generate
4. Displays the generated suggestions
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.backend.common.extensions import db
from src.backend.models import (
    User, Room, Seat, Booking, TemperatureReading, RoomEnergyState, SeatSuggestion
)
from src.main import app

BASE_URL = "http://localhost:5000"


def setup_mock_data():
    """Create mock data for testing"""
    print("\n=== Setting up mock data ===")
    
    with app.app_context():
        # Clear existing test data
        db.session.query(SeatSuggestion).delete()
        db.session.query(Booking).delete()
        db.session.query(TemperatureReading).delete()
        db.session.query(RoomEnergyState).delete()
        db.session.commit()

        rooms = db.session.query(Room).all()
        seats = db.session.query(Seat).all()
        
        # Create a test user
        print("Searching for test user...")
        user = db.session.query(User).filter_by(username="testuser").first()
        user.password = generate_password_hash("hashed_password")
        if not user:
            print("Creating test user...")
            user = User(
                username="testuser",
                password=generate_password_hash("hashed_password"), 
                first_name="Test",
                last_name="User",
                email="test@example.com",
                role="student"
            )
            db.session.add(user)
            db.session.flush()
        
        # Create historical bookings (past 30 days, same weekday/hour pattern)
        print("Creating historical bookings...")
        now = datetime.now()
        target_hour = 14  # 2 PM
        target_weekday = now.weekday()
        
        # Create bookings for the same weekday and hour, going back 90 days
        for days_back in range(0, 90, 7):  # Every week for 90 days
            booking_date = now - timedelta(days=days_back)
            if booking_date.weekday() == target_weekday:
                for seat in seats[:4]:  # Book first 4 seats
                    start_time = booking_date.replace(hour=target_hour, minute=0, second=0)
                    end_time = start_time + timedelta(hours=2)
                    booking = Booking(
                        user_id=user.id,
                        seat_id=seat.id,
                        start_time=start_time,
                        end_time=end_time,
                        status="completed"
                    )
                    db.session.add(booking)
        
        # Create temperature readings (last 30 days)
        print("Creating temperature readings...")
        for room in rooms:
            for days_back in range(30):
                reading_date = now - timedelta(days=days_back)
                # Simulate realistic temperature variations
                base_temp = 20 + (5 * days_back / 30)  # Gradually increase
                temp = base_temp + (2 if room.id == rooms[0].id else -1)  # Room variation
                reading = TemperatureReading(
                    room_id=room.id,
                    temperature=temp,
                    timestamp=reading_date
                )
                db.session.add(reading)
        
        # Create room energy states
        print("Creating room energy states...")
        state1 = RoomEnergyState(
            room_id=rooms[0].id,
            lights_on=True,
            ac_on=True,
            target_temperature=22.0,
            last_updated=now
        )
        state2 = RoomEnergyState(
            room_id=rooms[1].id,
            lights_on=False,
            ac_on=False,
            target_temperature=20.0,
            last_updated=now
        )
        db.session.add_all([state1, state2])
        
        db.session.commit()
        print(f"✓ Mock data created successfully")
        print(f"  - Bookings: {db.session.query(Booking).count()}")
        print(f"  - Temperature readings: {db.session.query(TemperatureReading).count()}")


def login_user(username: str, password: str) -> str:
    """Login and return JWT token"""
    print(f"\n=== Logging in user: {username} ===")
    
    response = requests.post(
        f"{BASE_URL}/login",
        json={"username": username, "password": password}
    )
    
    if response.status_code != 200:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None
    
    data = response.json()
    token = data.get("access_token")
    print(f"✓ Login successful, token obtained")
    return token


def generate_suggestions(token: str):
    """Call the /seat-suggestions/generate endpoint"""
    print(f"\n=== Generating seat suggestions ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # No JSON body - uses current date/hour
    response = requests.post(
        f"{BASE_URL}/seat-suggestions/generate",
        headers=headers
    )
    
    if response.status_code not in (200, 201):
        print(f"✗ Request failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None
    
    suggestions = response.json()
    print(f"✓ Generated {len(suggestions)} suggestions")
    return suggestions


def display_suggestions(suggestions: list):
    """Pretty-print suggestions"""
    print(f"\n=== Top Seat Suggestions ===")
    print(f"{'Rank':<5} {'Seat ID':<10} {'Score':<10} {'Reason':<50}")
    print("-" * 75)
    
    for rank, s in enumerate(suggestions[:5], 1):
        print(f"{rank:<5} {s['seat_id']:<10} {s['score']:<10.4f} {s['reason']:<50}")
    
    if len(suggestions) > 5:
        print(f"... and {len(suggestions) - 5} more suggestions")


def main():
    """Main test workflow
    
    Usage:
        python test_suggestions.py              # Full workflow (setup + generate)
        python test_suggestions.py setup        # Only setup mock data
        python test_suggestions.py generate     # Only generate suggestions (no setup)
    """
    print("=" * 75)
    print("SEAT SUGGESTIONS TEST SCRIPT")
    print("=" * 75)
    
    # Parse command line arguments
    mode = "full"  # full | setup | generate
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in ("setup", "generate", "full"):
            print(f"✗ Invalid mode: {mode}")
            print("  Use: setup, generate, or full (default)")
            return
    
    # Step 1: Setup mock data (if requested)
    if mode in ("setup", "full"):
        try:
            setup_mock_data()
        except Exception as e:
            print(f"✗ Error setting up mock data: {e}")
            if mode == "setup":
                return
            # Continue anyway if mode is "full"
    
    if mode == "setup":
        print("\n✓ Setup complete. You can now run: python test_suggestions.py generate")
        return
    
    # Give Flask time to initialize (optional sleep)
    import time
    time.sleep(1)
    
    # Step 2: Login user
    token = login_user("testuser", "hashed_password")
    if not token:
        print("✗ Cannot proceed without valid token")
        return
    
    # Step 3: Generate suggestions
    suggestions = generate_suggestions(token)
    if suggestions is None:
        print("✗ Failed to generate suggestions")
        return
    
    # Step 4: Display results
    display_suggestions(suggestions)
    
    print("\n" + "=" * 75)
    print("Test complete!")
    print("=" * 75)


if __name__ == "__main__":
    main()
