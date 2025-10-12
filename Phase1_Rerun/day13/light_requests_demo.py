import requests
import json

# Light Demo: Fetching Json from API
print("="*60)
print("Fetching JSON from API")
print("="*60)

try:
    #Public API - JSONPlaceholder
    response = requests.get('https://jsonplaceholder.typicode.com/users/1')

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        user = response.json()
        print(f"\n✓ User Data:")
        print(f"  Name: {user['name']}")
        print(f"  Email: {user['email']}")
        print(f"  City: {user['address']['city']}")

except requests.RequestExceptions as e:
    print(f" Error: {e}")

print("\n" + "="*60)
print("Fetching Multiple Posts")
print("=" *60)

try:
    response = requests.get('https://jsonplaceholder.typicode.com/posts?_limit=3')
    posts = response.json()
    
    print(f"\n✓ Retrieved {len(posts)} posts:")
    for post in posts:
        print(f"\n  Post #{post['id']}: {post['title'][:50]}...")

except requests.RequestException as e:
    print(f"❌ Error: {e}")
