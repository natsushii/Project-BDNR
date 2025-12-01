from bson.objectid import ObjectId
from datetime import datetime, timedelta

#User queries
def get_user_by_id(db,user_id):
    return db.users.find_one({'_id': ObjectId(user_id)})

def get_users_by_username(db,username):
    return db.users.find_one({'username': username})

def get_users_by_location (db, location, limit=20):
    return list(db.users.find(
        {'personal_info.location': {'$regex':location, '$options':'i'}},
        {'username':1, 'personal_info':1, 'stats':1}
        ).limit(limit))

def create_user(db, user_data):
    result = db.users.insert_one(user_data)
    return result.inserted_id

def update_user(db,user_id, update_data):
    if '_id' in update_data:
        del update_data['_id']
    result = db.users.update_one({'_id': ObjectId(user_id)}, {'$set':update_data})
    return result

def get_user_privacy_settings(db, user_id):
    return db.users.find_one(
        {'_id': ObjectId(user_id)},
        {'privacy_settings': 1, 'username': 1}
    )

def update_privacy_settings(db, user_id, privacy_data):
    result = db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'privacy_settings': privacy_data}}
    )
    return result


def get_notification_preferences(db, user_id):
    return db.users.find_one(
        {'_id': ObjectId(user_id)},
        {'notification_preferences': 1, 'username': 1}
    )


def update_notification_preferences(db, user_id, notification_data):
    result = db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'notification_preferences': notification_data}}
    )
    return result

#Post queries
def get_posts_by_date_range(db, user_id, start_date, end_date):
    return list(db.posts.find(
        {'user_id': ObjectId(user_id),
        'created_at': {
        '$gte': start_date,
        '$lte': end_date
        }
        }
    ).sort('created_at', -1))

def get_viral_posts(db,days=30, min_likes=10, limit=50):
    date_threshold = datetime.now() - timedelta(days=days)

    pipeline = [
        {
            '$match': {
                'created_at': {'$gte': date_threshold},
                'is_viral': True,
                'likes_count': {'$gte': min_likes}
            }
        },
        {
            '$lookup':{
                'from': 'users',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'user_info'
            }
        },
        {
            '$unwind': '$user_info'
        },
        {
            '$addFields':{
                'engagements_score':{
                    '$add': ['$likes_count', {'$multiply': ['$comments_count', 2]}]
                }
            }
        },
        {
            '$sort': {'engagement_score': -1}
        },
        {
            '$limit' : limit
        },
        {
            '$project': {
                '_id': 1,
                'description': 1,
                'created_at': 1,
                'location': 1,
                'hashtags': 1,
                'likes_count': 1,
                'comments_count': 1,
                'engagement_score': 1,
                'is_viral': 1,
                'user_info.username': 1,
                'user_info.personal_info.first_name': 1,
                'user_info.personal_info.last_name': 1
            }     
        }
    ]
    return list(db.posts.aggregate(pipeline))

def create_post(db,post_data):
    if post_data.get('likes_count', 0) >= 10:
        post_data['is_viral'] = True
        post_data['viral_detected_at'] = datetime.now()
    result = db.posts.insert_one(post_data)
    return result.inserted_id

# user_relationships queries
def get_user_following(db, user_id, limit = 100):
    pipeline = [
        {
            '$match': {
                'follower_id': ObjectId(user_id),
                'status': 'active'
            }
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'following_id',
                'foreignField': '_id',
                'as': 'followed_user'
            }
        },
        {
            '$unwind': '$followed_user'
        },
        {
            '$sort': {'followed_at': -1}
        },
        {
            '$limit': limit
        },
        {
            '$project': {
                '_id': 0,
                'followed_user_id': '$following_id',
                'username': '$followed_user.username',
                'full_name': {
                    '$concat': [
                        '$followed_user.personal_info.first_name',
                        ' ',
                        '$followed_user.personal_info.last_name'
                    ]
                },
                'location': '$followed_user.personal_info.location',
                'followed_at': 1
            }
        }
    ]
    
    return list(db.user_relationships.aggregate(pipeline))

#searched_history queries
def get_search_history(db, user_id, limit=10):
    pipeline = [
        {
            '$match': {'user_id': ObjectId(user_id)}
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'searched_user_id',
                'foreignField': '_id',
                'as': 'searched_user'
            }
        },
        {
            '$unwind': '$searched_user'
        },
        {
            '$sort': {'searched_at': -1}
        },
        {
            '$limit': limit
        },
        {
            '$project': {
                '_id': 0,
                'searched_user_id': 1,
                'searched_username': '$searched_user.username',
                'searched_at': 1
            }
        }
    ]
    
    return list(db.search_history.aggregate(pipeline))


def add_to_search_history(db, user_id, searched_user_id):
    search_entry = {
        'user_id': ObjectId(user_id),
        'searched_user_id': ObjectId(searched_user_id),
        'searched_at': datetime.now()
    }
    
    db.search_history.insert_one(search_entry)
    
    # Keep last 10
    all_searches = list(db.search_history.find(
        {'user_id': ObjectId(user_id)}
    ).sort('searched_at', -1))
    
    if len(all_searches) > 10:
        ids_to_delete = [s['_id'] for s in all_searches[10:]]
        db.search_history.delete_many({'_id': {'$in': ids_to_delete}})
    
    return True

#best_friends queries
def get_best_friends(db, user_id, limit=20):
    pipeline = [
        {
            '$match': {'user_id': ObjectId(user_id)}
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'friend_id',
                'foreignField': '_id',
                'as': 'friend'
            }
        },
        {
            '$unwind': '$friend'
        },
        {
            '$sort': {'position': 1}
        },
        {
            '$limit': limit
        },
        {
            '$project': {
                '_id': 0,
                'friend_id': 1,
                'username': '$friend.username',
                'full_name': {
                    '$concat': [
                        '$friend.personal_info.first_name',
                        ' ',
                        '$friend.personal_info.last_name'
                    ]
                },
                'added_at': 1
            }
        }
    ]
    
    return list(db.best_friends.aggregate(pipeline))


def add_best_friend(db, user_id, friend_id):
    # Not in the list
    existing = db.best_friends.find_one({
        'user_id': ObjectId(user_id),
        'friend_id': ObjectId(friend_id)
    })
    
    if existing:
        return None 
    
    best_friend_entry = {
        'user_id': ObjectId(user_id),
        'friend_id': ObjectId(friend_id),
        'added_at': datetime.now(),
    }
    
    result = db.best_friends.insert_one(best_friend_entry)
    return result.inserted_id


def remove_best_friend(db, user_id, friend_id):
    """Elimina un usuario de la lista de mejores amigos"""
    result = db.best_friends.delete_one({
        'user_id': ObjectId(user_id),
        'friend_id': ObjectId(friend_id)
    })
    return result

#saved_post queries
def get_saved_posts(db, user_id, limit=50):
    pipeline = [
        {
            '$match': {'user_id': ObjectId(user_id)}
        },
        {
            '$lookup': {
                'from': 'posts',
                'localField': 'post_id',
                'foreignField': '_id',
                'as': 'post'
            }
        },
        {
            '$unwind': '$post'
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'post.user_id',
                'foreignField': '_id',
                'as': 'post_author'
            }
        },
        {
            '$unwind': '$post_author'
        },
        {
            '$sort': {'saved_at': -1}
        },
        {
            '$limit': limit
        },
        {
            '$project': {
                '_id': 0,
                'post_id': '$post._id',
                'saved_at': 1,
                'collection_name': 1,
                'post_description': '$post.description',
                'post_created_at': '$post.created_at',
                'author_username': '$post_author.username',
                'likes_count': '$post.likes_count',
                'comments_count': '$post.comments_count'
            }
        }
    ]
    
    return list(db.saved_posts.aggregate(pipeline))


def save_post(db, user_id, post_id, collection_name="Favoritos"):
    # do not exists
    existing = db.saved_posts.find_one({
        'user_id': ObjectId(user_id),
        'post_id': ObjectId(post_id)
    })
    
    if existing:
        return None
    
    saved_entry = {
        'user_id': ObjectId(user_id),
        'post_id': ObjectId(post_id),
        'saved_at': datetime.now(),
        'collection_name': collection_name
    }
    
    result = db.saved_posts.insert_one(saved_entry)
    return result.inserted_id


def unsave_post(db, user_id, post_id):
    result = db.saved_posts.delete_one({
        'user_id': ObjectId(user_id),
        'post_id': ObjectId(post_id)
    })
    return result

#pipeline summary
def get_profile_summary(db, user_id):
    pipeline = [
        {
            '$match': {'_id': ObjectId(user_id)}
        },
        {
            '$lookup': {
                'from': 'posts',
                'localField': '_id',
                'foreignField': 'user_id',
                'as': 'user_posts'
            }
        },
        {
            '$lookup': {
                'from': 'user_relationships',
                'let': {'userId': '$_id'},
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {'$eq': ['$following_id', '$$userId']},
                                    {'$eq': ['$status', 'active']}
                                ]
                            }
                        }
                    }
                ],
                'as': 'followers'
            }
        },
        {
            '$lookup': {
                'from': 'user_relationships',
                'let': {'userId': '$_id'},
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {'$eq': ['$follower_id', '$$userId']},
                                    {'$eq': ['$status', 'active']}
                                ]
                            }
                        }
                    }
                ],
                'as': 'following'
            }
        },
        {
            '$addFields': {
                'viral_posts_count': {
                    '$size': {
                        '$filter': {
                            'input': '$user_posts',
                            'as': 'post',
                            'cond': {'$eq': ['$$post.is_viral', True]}
                        }
                    }
                },
                'total_likes': {'$sum': '$user_posts.likes_count'},
                'total_comments': {'$sum': '$user_posts.comments_count'},
                'avg_likes_per_post': {
                    '$cond': [
                        {'$gt': [{'$size': '$user_posts'}, 0]},
                        {'$divide': [{'$sum': '$user_posts.likes_count'}, {'$size': '$user_posts'}]},
                        0
                    ]
                }
            }
        },
        {
            '$project': {
                '_id': 1,
                'username': 1,
                'personal_info': 1,
                'stats': 1,
                'summary': {
                    'total_posts': {'$size': '$user_posts'},
                    'viral_posts_count': '$viral_posts_count',
                    'followers_count': {'$size': '$followers'},
                    'following_count': {'$size': '$following'},
                    'total_likes': '$total_likes',
                    'total_comments': '$total_comments',
                    'avg_likes_per_post': {'$round': ['$avg_likes_per_post', 2]},
                    'main_location': '$personal_info.location'
                }
            }
        }
    ]
    
    result = list(db.users.aggregate(pipeline))
    return result[0] if result else None