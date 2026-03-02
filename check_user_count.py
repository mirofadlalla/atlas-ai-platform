#!/usr/bin/env python3
"""
Quick utility to check number of users and display RAID structure improvements info
"""

from app.core.db import get_db_session
from app.models.user import Users
from sqlalchemy import func

def get_user_stats():
    """Get user statistics from the database"""
    db = get_db_session()
    try:
        # Total users
        total_users = db.query(func.count(Users.id)).scalar()
        
        # Users by approval status
        approved_users = db.query(func.count(Users.id)).filter(
            Users.approval_status == "approved"
        ).scalar()
        
        pending_users = db.query(func.count(Users.id)).filter(
            Users.approval_status == "pending"
        ).scalar()
        
        rejected_users = db.query(func.count(Users.id)).filter(
            Users.approval_status == "rejected"
        ).scalar()
        
        # Users by role
        admin_users = db.query(func.count(Users.id)).filter(
            Users.role == "admin"
        ).scalar()
        
        return {
            "total_users": total_users,
            "approved_users": approved_users,
            "pending_users": pending_users,
            "rejected_users": rejected_users,
            "admin_users": admin_users
        }
    finally:
        db.close()

def display_raid_improvements():
    """Display RAID structure improvements"""
    raid_improvements = {
        "RAID 0 (Striping)": [
            "✓ Improved performance (parallel read/write)",
            "✗ No fault tolerance"
        ],
        "RAID 1 (Mirroring)": [
            "✓ Full redundancy with mirrored data",
            "✓ High fault tolerance",
            "✗ 50% storage overhead"
        ],
        "RAID 5 (Striping with Parity)": [
            "✓ Good performance",
            "✓ Fault tolerance (can lose 1 drive)",
            "✓ Efficient storage (67% capacity)",
            "✓ Cost-effective"
        ],
        "RAID 6 (Dual Parity)": [
            "✓ Very high fault tolerance (can lose 2 drives)",
            "✓ Better for large drives",
            "✗ Slower write performance",
            "✗ More CPU overhead"
        ],
        "RAID 10 (1+0)": [
            "✓ Excellent performance",
            "✓ Very good fault tolerance",
            "✗ 50% storage overhead"
        ]
    }
    
    return raid_improvements

if __name__ == "__main__":
    print("=" * 70)
    print("ATLAS-AI: USER COUNT & RAID STRUCTURE ANALYSIS")
    print("=" * 70)
    
    # Get user statistics
    print("\n📊 USER STATISTICS:")
    print("-" * 70)
    try:
        stats = get_user_stats()
        print(f"  Total Users in System:        {stats['total_users']}")
        print(f"  ├─ Approved Users:            {stats['approved_users']}")
        print(f"  ├─ Pending Approval:          {stats['pending_users']}")
        print(f"  ├─ Rejected:                  {stats['rejected_users']}")
        print(f"  └─ Admin Users:               {stats['admin_users']}")
    except Exception as e:
        print(f"  ⚠️  Error connecting to database: {e}")
        print(f"     Make sure PostgreSQL is running and .env is configured correctly")
    
    # Display RAID improvements
    print("\n🔧 RAID STRUCTURE IMPROVEMENTS & CHARACTERISTICS:")
    print("-" * 70)
    raid_improvements = display_raid_improvements()
    
    for raid_type, improvements in raid_improvements.items():
        print(f"\n  {raid_type}:")
        for improvement in improvements:
            print(f"    {improvement}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION: RAID 5 or RAID 6 for production databases")
    print("=" * 70)
