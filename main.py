import falcon.asgi
import logging
from connect import get_mongo_db, get_cassandra_session, get_dgraph_client, test_connections
from MongoDB import resources

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware:
    async def process_request(self, req, resp):
        logger.info(f"Request: {req.method} {req.uri}")

    async def process_response(self, req, resp, resource, req_succeeded):
        logger.info(f"Response: {resp.status} for {req.method} {req.uri}")

class HealthCheckResource:
    async def on_get(self, req, resp):
        resp.media = {
            'status': 'OK',
            'service': 'Project-BDNR API',
            'version': '1.0.0'
        }
        resp.status = falcon.HTTP_200

app = falcon.asgi.App(middleware=[LoggingMiddleware()])

logger.info("Connecting Databases")
try:
    test_connections()
    logger.info("Databases connected correclty")
except Exception as e:
    logger.error(f"Failed connections: {e}")
    raise

mongo_db = get_mongo_db()
logger.info("MongoDB connected")

#verificando indices
logger.info("Cheking Index creation")
try:
    # Indexes Users
    mongo_db.users.create_index([("username", 1)], unique=True, background=True, name="username_unique")
    mongo_db.users.create_index([("email", 1)], unique=True, background=True, name="email_unique")
    mongo_db.users.create_index([("personal_info.location", 1)], background=True, name="location_search")

    # Indexes Post
    mongo_db.posts.create_index([("hashtags", 1)], background=True, name="hashtags_search")
    mongo_db.posts.create_index([("is_viral", 1)], background=True, name="is_viral_filter")
    mongo_db.posts.create_index([("location", 1)], background=True, name="location_filter")
    mongo_db.posts.create_index([("likes_count", 1)], background=True, name="likes_count_sort")

    # Indexes User_relationships
    mongo_db.user_relationships.create_index([("following_id", 1)], background=True, name="following_lookup")
    mongo_db.user_relationships.create_index([("follower_id", 1)], background=True, name="follower_lookup")
    mongo_db.user_relationships.create_index(
        [("follower_id", 1), ("following_id", 1)], 
        unique=True, 
        background=True,
        name="unique_relationship"
    )

    # Indexes Best_friends
    mongo_db.best_friends.create_index(
        [("user_id", 1), ("friend_id", 1)],
        background=True,
        name="search_friend"
    )
    mongo_db.best_friends.create_index(
        [("user_id", 1), ("friend_id", 1)],
        unique=True,
        background=True,
        name="unique_friendship"
    )

    # Indexes Saved_posts
    mongo_db.saved_posts.create_index(
        [("user_id", 1), ("saved_at", -1)],
        background=True,
        name="show_saved"
    )
    mongo_db.saved_posts.create_index(
        [("user_id", 1), ("post_id", 1)],
        unique=True,
        background=True,
        name="unique_saved_post"
    )

    # Indexes search_history
    mongo_db.search_history.create_index(
        [("user_id", 1), ("searched_at", -1)],
        background=True,
        name="show_recent"
    )
    mongo_db.search_history.create_index(
        [("searched_at", 1)],
        expireAfterSeconds=7776000,  # 90 días
        background=True,
        name="delete_after_90_days"
    )
    logger.info("Indexes created correclty")
except Exception as e:
    logger.warning(f"Failed verifying indexes")

# Health check
health_check = HealthCheckResource()

# Usuarios
user_resource = resources.UserResource(mongo_db)
users_resource = resources.UsersResource(mongo_db)
users_by_location = resources.UsersByLocationResource(mongo_db)

# Posts
posts_by_date = resources.PostsByDateRangeResource(mongo_db)
viral_posts = resources.ViralPostsResource(mongo_db)
posts_resource = resources.PostsResource(mongo_db)

# Seguimiento
user_following = resources.UserFollowingResource(mongo_db)

# Configuración
privacy_settings = resources.PrivacySettingsResource(mongo_db)
notification_preferences = resources.NotificationPreferencesResource(mongo_db)

# Funcionalidades especiales
search_history = resources.SearchHistoryResource(mongo_db)
best_friends = resources.BestFriendsResource(mongo_db)
saved_posts = resources.SavedPostsResource(mongo_db)
profile_summary = resources.ProfileSummaryResource(mongo_db)

app.add_route('/health', health_check)

#User
app.add_route('/mongo/users', users_resource)                       
app.add_route('/mongo/users/{user_id}', user_resource)                 
app.add_route('/mongo/users/location', users_by_location) 
app.add_route('/mongo/users/{user_id}/privacy', privacy_settings)   
app.add_route('/mongo/users/{user_id}/notifications', notification_preferences)  

# Post
app.add_route('/mongo/posts', posts_resource)                          
app.add_route('/mongo/posts/date-range', posts_by_date)                
app.add_route('/mongo/posts/viral', viral_posts)   

# relationships
app.add_route('/mongo/users/{user_id}/following', user_following) 
app.add_route('/mongo/users/{user_id}/search-history', search_history)     # GET, POST
app.add_route('/mongo/users/{user_id}/best-friends', best_friends)         # GET, POST, DELETE
app.add_route('/mongo/users/{user_id}/saved-posts', saved_posts)           # GET, POST, DELETE
app.add_route('/mongo/users/{user_id}/summary', profile_summary)   

logger.info("Routes complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )