#!/usr/bin/env python3
"""
Demo script to populate the index with sample data
"""
from database import IndexDatabase

def create_demo_data():
    """Create sample index entries"""
    db = IndexDatabase('demo_index.db')
    
    print("Creating demo index entries...")
    print()
    
    # Sample entries for a computer science textbook
    entries = [
        ("algorithm", "1:5"),
        ("algorithm", "1:12-15"),
        ("algorithm", "2:3"),
        ("array", "1:20"),
        ("array", "1:25-28"),
        ("binary search", "2:10-12"),
        ("binary tree", "3:5"),
        ("big O notation", "1:8"),
        ("complexity analysis", "1:8-10"),
        ("data structure", "1:18"),
        ("hash table", "2:30"),
        ("linked list", "2:15-20"),
        ("machine learning", "4:1-5"),
        ("neural network", "4:10-15"),
        ("queue", "2:25"),
        ("recursion", "3:1-8"),
        ("stack", "2:22-24"),
        ("sorting", "2:5-9"),
        ("tree traversal", "3:8-12"),
    ]
    
    added = 0
    duplicates = 0
    
    for term, ref in entries:
        if db.add_entry(term, ref):
            print(f"✓ Added: {term} → {ref}")
            added += 1
        else:
            print(f"⚠ Skipped (duplicate): {term} → {ref}")
            duplicates += 1
    
    print()
    print("=" * 60)
    print(f"Demo data created!")
    print(f"  Added: {added} entries")
    print(f"  Skipped: {duplicates} duplicates")
    print(f"  Database: demo_index.db")
    print("=" * 60)
    print()
    print("Try these commands:")
    print("  python index_cli.py -d demo_index.db list")
    print("  python index_cli.py -d demo_index.db search 'tree'")
    print("  python index_cli.py -d demo_index.db export -o demo_index.tex")

if __name__ == '__main__':
    create_demo_data()
