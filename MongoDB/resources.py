import falcon
from bson.objectid import ObjectId
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MongoDB import queries

def convert_objectid_to_str(doc):
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [convert_objectid_to_str(item) for item in doc]
    
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, dict):
                doc[key] = convert_objectid_to_str(value)
            elif isinstance(value, list):
                doc[key] = [convert_objectid_to_str(item) if isinstance(item, (dict, ObjectId)) else item for item in value]
        return doc
    
    if isinstance(doc, ObjectId):
        return str(doc)
    
    return doc

#user
class UserResource:

    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        user = queries.get_user_by_id(self.db, user_id)
        
        if user:
            user = convert_objectid_to_str(user)
            resp.media = user
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'User not found'}
    
    async def on_put(self, req, resp, user_id):
        try:
            update_data = await req.media
            result = queries.update_user(self.db, user_id, update_data)
            
            if result.matched_count == 0:
                resp.status = falcon.HTTP_404
                resp.media = {'error': 'User not found'}
            else:
                # Obtener el usuario actualizado
                updated_user = queries.get_user_by_id(self.db, user_id)
                updated_user = convert_objectid_to_str(updated_user)
                resp.media = updated_user
                resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))
    
class UsersResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp):
        username = req.get_param('username')
        
        if username:
            user = queries.get_user_by_username(self.db, username)
            if user:
                user = convert_objectid_to_str(user)
                resp.media = user
                resp.status = falcon.HTTP_200
            else:
                resp.status = falcon.HTTP_404
                resp.media = {'error': 'User not found'}
        else:
            resp.media = {'message': 'Use ?username=XXX to search for a user'}
            resp.status = falcon.HTTP_200
    
    async def on_post(self, req, resp):
        try:
            user_data = await req.media
            inserted_id = queries.create_user(self.db, user_data)
            
            # Obtener el usuario creado
            user = queries.get_user_by_id(self.db, str(inserted_id))
            user = convert_objectid_to_str(user)
            
            resp.media = user
            resp.status = falcon.HTTP_201
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

class UsersByLocationResource:
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp):
        try:
            location = req.get_param('location', required=True)
            limit = req.get_param_as_int('limit', default=20)
            
            users = queries.get_users_by_location(self.db, location, limit)
            users = convert_objectid_to_str(users)
            
            resp.media = {
                'location': location,
                'count': len(users),
                'users': users
            }
            resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

class PrivacySettingsResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        settings = queries.get_user_privacy_settings(self.db, user_id)
        
        if settings:
            settings = convert_objectid_to_str(settings)
            resp.media = settings
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'User not found'}
    
    async def on_put(self, req, resp, user_id):
        try:
            privacy_data = await req.media
            result = queries.update_privacy_settings(self.db, user_id, privacy_data)
            
            if result.matched_count == 0:
                resp.status = falcon.HTTP_404
                resp.media = {'error': 'User not found'}
            else:
                # Obtener configuración actualizada
                settings = queries.get_user_privacy_settings(self.db, user_id)
                settings = convert_objectid_to_str(settings)
                resp.media = settings
                resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))


class NotificationPreferencesResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        preferences = queries.get_notification_preferences(self.db, user_id)
        
        if preferences:
            preferences = convert_objectid_to_str(preferences)
            resp.media = preferences
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'User not found'}
    
    async def on_put(self, req, resp, user_id):
        try:
            notification_data = await req.media
            result = queries.update_notification_preferences(self.db, user_id, notification_data)
            
            if result.matched_count == 0:
                resp.status = falcon.HTTP_404
                resp.media = {'error': 'User not found'}
            else:
                # Obtener preferencias actualizadas
                preferences = queries.get_notification_preferences(self.db, user_id)
                preferences = convert_objectid_to_str(preferences)
                resp.media = preferences
                resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

#post
class PostsByDateRangeResource:

    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp):
        try:
            user_id = req.get_param('user_id', required=True)
            start_date_str = req.get_param('start_date', required=True)
            end_date_str = req.get_param('end_date', required=True)
            
            # Convertir strings a datetime
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            
            posts = queries.get_posts_by_date_range(self.db, user_id, start_date, end_date)
            posts = convert_objectid_to_str(posts)
            
            resp.media = {
                'user_id': user_id,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'count': len(posts),
                'posts': posts
            }
            resp.status = falcon.HTTP_200
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))


class ViralPostsResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp):
        days = req.get_param_as_int('days', default=30)
        min_likes = req.get_param_as_int('min_likes', default=10)
        limit = req.get_param_as_int('limit', default=50)
        
        viral_posts = queries.get_viral_posts(self.db, days, min_likes, limit)
        viral_posts = convert_objectid_to_str(viral_posts)
        
        resp.media = {
            'criteria': {
                'days': days,
                'min_likes': min_likes,
                'limit': limit
            },
            'count': len(viral_posts),
            'posts': viral_posts
        }
        resp.status = falcon.HTTP_200


class PostsResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_post(self, req, resp):
        try:
            post_data = await req.media
            
            # Convertir user_id a ObjectId si viene como string
            if 'user_id' in post_data and isinstance(post_data['user_id'], str):
                post_data['user_id'] = ObjectId(post_data['user_id'])
            
            # Convertir tagged_users a ObjectIds
            if 'tagged_users' in post_data:
                post_data['tagged_users'] = [
                    ObjectId(uid) if isinstance(uid, str) else uid 
                    for uid in post_data['tagged_users']
                ]
            
            # Asegurar que tenga created_at
            if 'created_at' not in post_data:
                post_data['created_at'] = datetime.now()
            
            inserted_id = queries.create_post(self.db, post_data)
            
            # Obtener el post creado
            post = self.db.posts.find_one({'_id': inserted_id})
            post = convert_objectid_to_str(post)
            
            resp.media = post
            resp.status = falcon.HTTP_201
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

#user_relationships
class UserFollowingResource:
    """Recurso para obtener usuarios seguidos"""
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        """GET /mongo/users/{user_id}/following - Obtener usuarios seguidos"""
        limit = req.get_param_as_int('limit', default=100)
        following = queries.get_user_following(self.db, user_id, limit)
        following = convert_objectid_to_str(following)
        
        resp.media = {
            'user_id': user_id,
            'count': len(following),
            'following': following
        }
        resp.status = falcon.HTTP_200

#search_history
class SearchHistoryResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        limit = req.get_param_as_int('limit', default=10)
        history = queries.get_search_history(self.db, user_id, limit)
        history = convert_objectid_to_str(history)
        
        resp.media = {
            'user_id': user_id,
            'count': len(history),
            'history': history
        }
        resp.status = falcon.HTTP_200
    
    async def on_post(self, req, resp, user_id):
        try:
            data = await req.media
            searched_user_id = data.get('searched_user_id')
            
            if not searched_user_id:
                raise falcon.HTTPBadRequest(description='searched_user_id is required')
            
            queries.add_to_search_history(self.db, user_id, searched_user_id)
            
            resp.media = {'success': True, 'message': 'Added to search history'}
            resp.status = falcon.HTTP_201
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

#best_friends
class BestFriendsResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        limit = req.get_param_as_int('limit', default=20)
        best_friends = queries.get_best_friends(self.db, user_id, limit)
        best_friends = convert_objectid_to_str(best_friends)
        
        resp.media = {
            'user_id': user_id,
            'count': len(best_friends),
            'best_friends': best_friends
        }
        resp.status = falcon.HTTP_200
    
    async def on_post(self, req, resp, user_id):
        try:
            data = await req.media
            friend_id = data.get('friend_id')
            
            if not friend_id:
                raise falcon.HTTPBadRequest(description='friend_id is required')
            
            inserted_id = queries.add_best_friend(self.db, user_id, friend_id)
            
            if inserted_id is None:
                resp.media = {'error': 'User already in best friends list'}
                resp.status = falcon.HTTP_409
            else:
                resp.media = {'success': True, 'message': 'Best friend added'}
                resp.status = falcon.HTTP_201
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))
    
    async def on_delete(self, req, resp, user_id):
        try:
            friend_id = req.get_param('friend_id', required=True)
            result = queries.remove_best_friend(self.db, user_id, friend_id)
            
            if result.deleted_count > 0:
                resp.media = {'success': True, 'message': 'Best friend removed'}
                resp.status = falcon.HTTP_200
            else:
                resp.status = falcon.HTTP_404
                resp.media = {'error': 'Best friend not found'}
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

#saved_post
class SavedPostsResource:
    
    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        limit = req.get_param_as_int('limit', default=50)
        saved_posts = queries.get_saved_posts(self.db, user_id, limit)
        saved_posts = convert_objectid_to_str(saved_posts)
        
        resp.media = {
            'user_id': user_id,
            'count': len(saved_posts),
            'saved_posts': saved_posts
        }
        resp.status = falcon.HTTP_200
    
    async def on_post(self, req, resp, user_id):
        try:
            data = await req.media
            post_id = data.get('post_id')
            collection_name = data.get('collection_name', 'Favoritos')
            
            if not post_id:
                raise falcon.HTTPBadRequest(description='post_id is required')
            
            inserted_id = queries.save_post(self.db, user_id, post_id, collection_name)
            
            if inserted_id is None:
                resp.media = {'error': 'Post already saved'}
                resp.status = falcon.HTTP_409
            else:
                resp.media = {'success': True, 'message': 'Post saved'}
                resp.status = falcon.HTTP_201
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))
    
    async def on_delete(self, req, resp, user_id):
        try:
            post_id = req.get_param('post_id', required=True)
            result = queries.unsave_post(self.db, user_id, post_id)
            
            if result.deleted_count > 0:
                resp.media = {'success': True, 'message': 'Post unsaved'}
                resp.status = falcon.HTTP_200
            else:
                resp.status = falcon.HTTP_404
                resp.media = {'error': 'Saved post not found'}
        except Exception as e:
            raise falcon.HTTPBadRequest(description=str(e))

#managing pipeline
class ProfileSummaryResource:

    def __init__(self, db):
        self.db = db
    
    async def on_get(self, req, resp, user_id):
        summary = queries.get_profile_summary(self.db, user_id)
        
        if summary:
            summary = convert_objectid_to_str(summary)
            resp.media = summary
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_404
            resp.media = {'error': 'User not found'}
