from connect import get_mongo_db, get_cassandra_session, get_dgraph_client
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker('es_MX')

def generate_fake_data():

    #generamos usuarios
    users = []
    num_users = 100

    for i in range(num_users):
        user = {
            "id": i, 
            "username": fake.user_name() + str(i),
            "email": fake.email(),
            "created_at": fake.date_time_between(start_date='-1y', end_date='now'),
            "personal_info": {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "birth_date": datetime.combine(fake.date_of_birth(minimum_age=18, maximum_age=60),datetime.min.time()),
                "pronouns": random.choice(["he/him", "she/her", "they/them"]),
                "location": fake.city() + ", Jalisco"
            },
            "privacy_settings": {
                "is_private": random.choice([True, False]),
                "allow_story_replies": random.choice([True, False]),
                "allow_comments": random.choice(["everyone", "followers", "none"]),
                "blocked_users": []
            },
            "notification_preferences": {
                "language": "es",
                "allow_notifications": random.choice([True, False]),
                "dm_notifications": random.choice([True, False]),
                "allowed_notification_users": []
            },
            "stats": {
                "total_posts": 0,
                "followers_count": 0,
                "following_count": 0,
                "saved_posts_count": 0
            }
        }
        users.append(user)

    #posts
    posts = []
    num_posts = 500
    
    hashtags_populares = ["MongoDB", "Tech", "Coding", "ITESO", "Guadalajara", "Python", "Database", "NoSQL", "Design", "Art"]
    
    for i in range(num_posts):
        post = {
            "id": i,
            "user_id": random.randint(0, num_users - 1),
            "description": fake.text(max_nb_chars=280),
            "created_at": fake.date_time_between(start_date='-6m', end_date='now'),
            "location": random.choice(["Guadalajara", "Zapopan", "Tlaquepaque", "Tonalá"]),
            "hashtags": random.sample(hashtags_populares, k=random.randint(1, 4)),
            "tagged_users": random.sample(range(num_users), k=random.randint(0, 3)),
            "likes_count": random.randint(0, 150),
            "comments_count": random.randint(0, 80),
            "is_viral": False
        }
        
        # Marcar como viral
        if post["likes_count"] >= 10:
            post["is_viral"] = True
            post["viral_detected_at"] = post["created_at"]
        
        posts.append(post)
    
    viral_count = sum(1 for p in posts if p["is_viral"])

    #relaciones
    relationships = []
    for user_id in range(num_users):
            num_following = random.randint(10, 30)
            following_users = random.sample([uid for uid in range(num_users) if uid != user_id], 
                                        k=min(num_following, num_users - 1))
            
            for followed_id in following_users:
                relationship = {
                    "follower_id": user_id,
                    "following_id": followed_id,
                    "followed_at": fake.date_time_between(start_date='-1y', end_date='now'),
                    "status": "active"
                }
                relationships.append(relationship)
    
    #lista de mejores amigos
    best_friends = []
    
    for user_id in range(num_users):
        num_best_friends = random.randint(5, 10)
        friend_ids = random.sample([uid for uid in range(num_users) if uid != user_id], 
                                   k=min(num_best_friends, num_users - 1))
        
        for friend_id in friend_ids:
            bf = {
                "user_id": user_id,
                "friend_id": friend_id,
                "added_at": fake.date_time_between(start_date='-6m', end_date='now'),
            }
            best_friends.append(bf)
    
    #post guardados
    saved_posts = []
    
    for user_id in range(num_users):
        num_saved = random.randint(8, 20)
        saved_post_ids = random.sample(range(num_posts), k=min(num_saved, num_posts))
        
        for post_id in saved_post_ids:
            saved = {
                "user_id": user_id,
                "post_id": post_id,
                "saved_at": fake.date_time_between(start_date='-3m', end_date='now'),
                "collection_name": random.choice(["Favoritos", "Leer después", "Inspiración", "Trabajo"])
            }
            saved_posts.append(saved)
    
    #historal de busqueda
    search_history = []
    
    for user_id in range(num_users):
        num_searches = random.randint(8, 15)
        searched_users = random.sample([uid for uid in range(num_users) if uid != user_id], 
                                      k=min(num_searches, num_users - 1))
        
        for searched_user_id in searched_users:
            search = {
                "user_id": user_id,
                "searched_user_id": searched_user_id,
                "searched_at": fake.date_time_between(start_date='-2m', end_date='now')
            }
            search_history.append(search)
    
    return {
        'users': users,
        'posts': posts,
        'relationships': relationships,
        'best_friends': best_friends,
        'saved_posts': saved_posts,
        'search_history': search_history
    }

def populate_mongodb(data):
    db = get_mongo_db()
    print("Llenando Mongo ...")

    #eliminamos datos anteriores para evitar confusiones
    db.users.delete_many({})
    db.posts.delete_many({})
    db.user_relationships.delete_many({})
    db.best_friends.delete_many({})
    db.saved_posts.delete_many({})
    db.search_history.delete_many({})

    #insertar usuarios
    result = db.users.insert_many(data['users'])
    user_object_ids = result.inserted_ids
    user_id_map = {i: user_object_ids[i] for i in range(len(user_object_ids))}

    #insertar post
    posts_for_mongo = []
    for post in data['posts']:
        post_copy = post.copy()
        post_copy['user_id'] = user_id_map[post['user_id']]
        post_copy['tagged_users'] = [user_id_map[uid] for uid in post['tagged_users']]
        del post_copy['id']
        posts_for_mongo.append(post_copy)
    
    result = db.posts.insert_many(posts_for_mongo)
    post_object_ids = result.inserted_ids
    post_id_map = {i: post_object_ids[i] for i in range(len(post_object_ids))}

    #insertar User_relationships
    relationships_for_mongo = []
    for rel in data['relationships']:
        rel_copy = rel.copy()
        rel_copy['follower_id'] = user_id_map[rel['follower_id']]
        rel_copy['following_id'] = user_id_map[rel['following_id']]
        relationships_for_mongo.append(rel_copy)
    
    if relationships_for_mongo:
        db.user_relationships.insert_many(relationships_for_mongo)
    
    #insertar mejores amigos
    best_friends_for_mongo = []
    for bf in data['best_friends']:
        bf_copy = bf.copy()
        bf_copy['user_id'] = user_id_map[bf['user_id']]
        bf_copy['friend_id'] = user_id_map[bf['friend_id']]
        best_friends_for_mongo.append(bf_copy)
    
    if best_friends_for_mongo:
        db.best_friends.insert_many(best_friends_for_mongo)
    
    #insertar saved_post
    saved_posts_for_mongo = []
    for saved in data['saved_posts']:
        saved_copy = saved.copy()
        saved_copy['user_id'] = user_id_map[saved['user_id']]
        saved_copy['post_id'] = post_id_map[saved['post_id']]
        saved_posts_for_mongo.append(saved_copy)
    
    if saved_posts_for_mongo:
        db.saved_posts.insert_many(saved_posts_for_mongo)
    
    #insertar historial de busqueda
    search_history_for_mongo = []
    for search in data['search_history']:
        search_copy = search.copy()
        search_copy['user_id'] = user_id_map[search['user_id']]
        search_copy['searched_user_id'] = user_id_map[search['searched_user_id']]
        search_history_for_mongo.append(search_copy)
    
    if search_history_for_mongo:
        db.search_history.insert_many(search_history_for_mongo)
    
    #Creamos index
    try:
        db.users.create_index([("username", 1)], unique=True, name="username_unique")
        db.users.create_index([("email", 1)], unique=True, name="email_unique")
        db.users.create_index([("personal_info.location", 1)], name="location_search")

    # Indexes Post
        db.posts.create_index([("hashtags", 1)], name="hashtags_search")
        db.posts.create_index([("is_viral", 1)], name="is_viral_filter")
        db.posts.create_index([("location", 1)], name="location_filter")
        db.posts.create_index([("likes_count", 1)], name="likes_count_sort")

    # Indexes User_relationships
        db.user_relationships.create_index([("following_id", 1)], name="following_lookup")
        db.user_relationships.create_index([("follower_id", 1)], name="follower_lookup")
        db.user_relationships.create_index(
            [("follower_id", 1), ("following_id", 1)], 
            unique=True, 
            name="unique_relationship"
        )

    # Indexes Best_friends
        db.best_friends.create_index(
            [("user_id", 1), ("friend_id", 1)],
            name="search_friend"
        )
        db.best_friends.create_index(
            [("user_id", 1), ("friend_id", 1)],
            unique=True,
            name="unique_friendship"
        )

    # Indexes Saved_posts
        db.saved_posts.create_index(
            [("user_id", 1), ("saved_at", -1)],
            name="show_saved"
        )
        db.saved_posts.create_index(
            [("user_id", 1), ("post_id", 1)],
            unique=True,
            name="unique_saved_post"
        )

    # Indexes search_history
        db.search_history.create_index(
            [("user_id", 1), ("searched_at", -1)],
            name="show_recent"
        )
        db.search_history.create_index(
            [("searched_at", 1)],
            expireAfterSeconds=7776000,
            name="delete_after_90_days"
        )    
        print ("Indexes created correctly")

    except Exception as e:
        print("Indexes creation failes\n")

    return user_id_map, post_id_map

#def populate_cassandra():

#def populate_dgraph():
    
def main():

    data = generate_fake_data()

    populate_mongodb(data)
    #populate_cassandra()
   #populate_dgraph()

    print("Datos completos en todas las bases de datos")

if __name__=="__main__":
    main()