import argparse
import logging
import os
import requests
import json
import sys
from datetime import datetime, timedelta

API_BASE_URL = os.getenv("PROJECT_BDNR_API_URL", "http://localhost:8000")

def print_header():
    print("="*50)
    print("Social Media Project App")
    print("="*50)

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

def health_check():
    print_header
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("Server working correctly")
            print_json(response.json())
        else:
            print(f"Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Server Failed. Run main.py")
    
def search_user():
    print("\nSearch Username\n")
    
    username = input("Username: ").strip()
    
    if not username:
        print("Please enter a valid username")
        return
    
    try:
        response = requests.get(f"{API_BASE_URL}/mongo/users", params={'username': username})
        
        if response.status_code == 200:
            user = response.json()
            print(f"User found: {username}\n")
            print(f"ID: {user.get('_id')}")
            print(f"Username: {user.get('username')}")
            print(f"Email: {user.get('email')}")
            
            personal = user.get('personal_info', {})
            print(f"Name: {personal.get('first_name')} {personal.get('last_name')}")
            print(f"Location: {personal.get('location')}")
            print(f"Birthday: {personal.get('birth_date', 'N/A')[:10]}")
            
            print("\nStadistics:")
            stats = user.get('stats', {})
            print(f"   • Posts: {stats.get('total_posts', 0)}")
            print(f"   • Followers: {stats.get('followers_count', 0)}")
            print(f"   • Following: {stats.get('following_count', 0)}")
            
        elif response.status_code == 404:
            print(f"User not found {username}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
def viral_posts():
    print("\nViral Post\n")
    
    try:
        days = input("Days to search").strip()
        days = int(days) if days else 30
        
        min_likes = input("Minimum likes (default 10) ").strip()
        min_likes = int(min_likes) if min_likes else 10
        
        limit = input("Limit results (default 10)").strip()
        limit = int(limit) if limit else 10
        
    except ValueError:
        print("Error, using default data")
        days, min_likes, limit = 30, 10, 10
    
    print(f"   Criteria: last {days} days, minimum {min_likes} likes\n")
    
    try:
        params = {'days': days, 'min_likes': min_likes, 'limit': limit}
        response = requests.get(f"{API_BASE_URL}/mongo/posts/viral", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} viral post\n")
            
            for i, post in enumerate(data['posts'], 1):
                print(f"{i}.Post ID: {post.get('_id')}")
                user_info = post.get('user_info', {})
                print(f"   User: {user_info.get('username', 'N/A')}")
                print(f"   Likes: {post.get('likes_count', 0)}")
                print(f"   Comments: {post.get('comments_count', 0)}")
                print(f"   Engagement: {post.get('engagement_score', 0)}")
                desc = post.get('description', '')
                print(f"   {desc[:80]}...")
                print()
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def users_by_location():
    print("\nUsers by location\n")
    
    location = input("Enter a location (ej: Guadalajara, Zapopan, Jalisco): ").strip()
    
    if not location:
        print("Please enter a valid location")
        return
    
    try:
        limit = input("Limit results (default 20): ").strip()
        limit = int(limit) if limit else 20
    except ValueError:
        limit = 20
    
    try:
        params = {'location': location, 'limit': limit}
        response = requests.get(f"{API_BASE_URL}/mongo/users/location", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} users in {data['location']}\n")
            
            for i, user in enumerate(data['users'], 1):
                personal = user.get('personal_info', {})
                print(f"{i}. {user.get('username')}")
                print(f"    {personal.get('location')}")
                print(f"    Posts: {user.get('stats', {}).get('total_posts', 0)}")
                print()
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def profile_summary():
    print("\nProfile Summary\n")
    
    user_id = input("Enter a user ID ").strip()
    
    if not user_id:
        print("Please enter a valid ID")
        return

    try:
        response = requests.get(f"{API_BASE_URL}/mongo/users/{user_id}/summary")
        
        if response.status_code == 200:
            data = response.json()
            print("Resumen del perfil\n")
            
            print(f"User: {data.get('username', 'N/A')}")
            personal = data.get('personal_info', {})
            print(f"Name: {personal.get('first_name')} {personal.get('last_name')}")
            print(f"Location: {personal.get('location')}")
            
            summary = data.get('summary', {})
            print(f"\nStadistics")
            print(f"   • Total Posts: {summary.get('total_posts', 0)}")
            print(f"   • Viral Posts: {summary.get('viral_posts_count', 0)}")
            print(f"   • Followers: {summary.get('followers_count', 0)}")
            print(f"   • Following: {summary.get('following_count', 0)}")
            print(f"   • Total likes: {summary.get('total_likes', 0)}")
            print(f"   • Total comments: {summary.get('total_comments', 0)}")
            print(f"   • Average likes/post: {summary.get('avg_likes_per_post', 0)}")
            print(f"   • Location: {summary.get('main_location', 'N/A')}")
        elif response.status_code == 404:
            print("Usuario no encontrado")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def best_friends():
    print("\nBest Friends List\n")
    
    user_id = input("Enter a User ID ").strip()
    
    if not user_id:
        print("Please enter a valid ID")
        return
    
    try:
        limit = input("Limit results (default 20): ").strip()
        limit = int(limit) if limit else 20
    except ValueError:
        limit = 20

    try:
        params = {'limit': limit}
        response = requests.get(f"{API_BASE_URL}/mongo/users/{user_id}/best-friends", params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Best Friend List: {data['count']}\n")
            
            for i, friend in enumerate(data['best_friends'], 1):
                print(f"{i}.Username: {friend.get('username')}")
                print(f" Name: {friend.get('full_name')}")
                print(f" Date added: {friend.get('added_at', 'N/A')[:10]}")
                print()
        elif response.status_code == 404:
            print("Usuario no encontrado")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def get_user_id_helper():
    print("\nGet username ID\n")
    
    username = input("Enter username: ").strip()
    
    if not username:
        print("Please enter a valid username")
        return
    
    try:
        response = requests.get(f"{API_BASE_URL}/mongo/users", params={'username': username})
        
        if response.status_code == 200:
            user = response.json()
            user_id = user.get('_id')
            print("User Found\n")
            print(f"Username: {user.get('username')}")
            print(f"User ID: {user_id}")
        elif response.status_code == 404:
            print(f"User not found: {username}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def show_menu():
    print_header()
    print("\nMENU\n")
    print("1. Health Server Check")
    print("2. Search user by username")
    print("3. Viral Posts")
    print("4. Search user by location")
    print("5. Profile Summasy")
    print("6. Best Friend list")
    print("7. Get user ID")
    print("8. Exit")
    print("\n" + "=" * 50)

def main():
    while True:
        show_menu()
        opcion = input("\nEnter an option 1 - 8: ").strip()
        
        if opcion == "1":
            health_check()
        elif opcion == "2":
            search_user()
        elif opcion == "3":
            viral_posts()
        elif opcion == "4":
            users_by_location()
        elif opcion == "5":
            profile_summary()
        elif opcion == "6":
            best_friends()
        elif opcion == "7":
            get_user_id_helper()
        elif opcion == "8":
            print_header()
            print("\nClosing\n")
            sys.exit(0)
        else:
            print("Please enter a valid option")

if __name__ == "__main__":
    main()