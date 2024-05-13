from sqlite3 import IntegrityError
from flask import Flask, request
from flask_restful import Resource, Api
from peewee import SqliteDatabase, Model, CharField, TextField
from flask_cors import CORS
import datetime
from peewee import *
import jwt



app = Flask(__name__)


# Set the secret key to some random bytes. Keep this value secret!
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'



from flask_session import Session
from flask import session
Session(app)

cors = CORS(app)



# Create a new Flask app and API

api = Api(app)

# Create a SQLite database and model for users
db = SqliteDatabase('users.db')

class User(Model):
    username = CharField(unique=True)
    password = CharField()

    class Meta:
        database = db
    
    def following(self):
        """The users that people follow"""
        return (
            User.select().join(
                Relationship, on=Relationship.to_user
            ).where(
                Relationship.from_user == self
            )
        )

    def followers(self):
        """Users that follow people."""
        return (
            User.select().join(
                Relationship, on=Relationship.from_user
            ).where(
                Relationship.to_user == self
            )
        )


class Relationship(Model):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='related_to')

    class Meta:
        database = db
        indexes = (
            (('from_user', 'to_user'), True),
        )
    
class Post(Model):
    user = CharField()
    title = CharField()
    content = TextField()
    imgurl = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

# Create a table for users
with db:
    db.create_tables([User, Post, Relationship])

# Define a resource for user registration
class Register(Resource):
    def post(self):
        # Get the username and password from the request
        username = request.json.get('username')
        password = request.json.get('password')

        # Create a new user in the database
        try:
            user = User.create(username=username, password=password)
        except IntegrityError:
            return {'message': 'Username already exists'}, 400

        return {'message': 'User created successfully'}, 201

# Define a resource for user login


class Login(Resource):
    def post(self):
        # Get the username and password from the request
        username = request.json.get('username')
        password = request.json.get('password')

        ##TOken based authentication
        payload = {'username': username}
        jwt_token = jwt.encode(payload, 'secret_key', algorithm='HS256')
        resp = make_response({'message': 'Login successful'})
        resp.set_cookie('jwt_token', jwt_token)

        # Find the user in the database
        try:
            user = User.get(User.username == username)
        except User.DoesNotExist:
            return {'message': 'Invalid credentials'}, 401

        # Check if the password is correct
        if user.password != password:
            return {'message': 'Invalid credentials'}, 401
        
        # Store the user ID in the session
        session['user_id'] = user.id

        return {'message': 'Login successful'}, 200
    
# Define a resource for creating a new post
class AddPost(Resource):

    def post(self):
        # Check if the user is logged in
        # if 'user_id' not in session:
        #     return {'message': 'Unauthorized'}, 401
        
        # Get the user, title, and content from the request
        user = request.json.get('user')
        title = request.json.get('title')
        content = request.json.get('content')
        imgurl = request.json.get('imgurl')

        # Create a new post in the database
        post = Post.create(user= user, title=title, content=content, imgurl = imgurl)

        return {'message': 'Post created successfully'}, 201
    
class EditPost(Resource):
    def post(self):
        # Check if the user is logged in
        # if 'user_id' not in session:
        #     return {'message': 'Unauthorized'}, 401

        # Get the updated title and content from the request
        print("jihihi")
        post_id = request.json.get("post_id")
        title = request.json.get('title')
        content = request.json.get('content')
        imgurl = request.json.get('imgurl')

        # Find the post to be updated
        try:
            post = Post.get(Post.id == post_id)
        except Post.DoesNotExist:
            return {'message': 'Post not found'}, 404

        # Update the post with the new title and content
        post.title = title
        post.content = content
        post.imgurl = imgurl
        post.save()

        return {'message': 'Post updated successfully'}, 200
    
class DeletePost(Resource):
    def delete(self, post_id):
        # Check if the user is logged in
        # if 'user_id' not in session:
        #     return {'message': 'Unauthorized'}, 401

        # Find the post to be deleted
        try:
            post = Post.get(Post.id == post_id)
        except Post.DoesNotExist:
            return {'message': 'Post not found'}, 404

        # Delete the post
        post.delete_instance()

        return {'message': 'Post deleted successfully'}, 200
    
class Search(Resource):
    def post(self):
        search = request.json.get("username")
        print(search)
        try:
            user = User.get(User.username == search)
        except DoesNotExist:
            return {'message': 'Invalid username'}, 401
        else:
            return {'message': 'User Found : )'}, 201
    

# Define a resource for fetching all posts as a feed
class Feed(Resource):
    def get(self):
        # Get all posts from the database
        posts = Post.select()   
            

        # Create a list of post dictionaries
        post_list = []
        for post in posts:
            post_dict = {'id': post.id,'timestamp':post.timestamp.isoformat(), 'user': post.user, 'title': post.title, 'content': post.content, 'imgurl': post.imgurl}
            post_list.append(post_dict)

        return {'posts': post_list}, 200
    
# Profile custom feed
class Profile(Resource):
    def get(self, username):
        # Get all posts from the database
        posts = Post.select().where(Post.user == username) 
            

        # Create a list of post dictionaries
        post_list = []
        for post in posts:
            post_dict = {'id': post.id,'timestamp':post.timestamp.isoformat(), 'user': post.user, 'title': post.title, 'content': post.content, 'imgurl': post.imgurl}
            post_list.append(post_dict)

        return {'posts': post_list}, 200
    

import csv
from flask import make_response

class DownloadPosts(Resource):
    def get(self,username):
        #username = request.json.get("username")
        # query the database for all posts by the user
        #user_posts = Post.objects.filter(user_id=user_id)
        stream = Post.select().where(Post.user == username)

        # create a new CSV file to store the posts
        with open('user_posts.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Post ID', 'User ID', 'Title','Content','Image', 'Date'])

            # iterate through the posts and write them to the CSV file
            for post in stream:
                writer.writerow([post.id, post.user, post.title,post.content,post.imgurl,post.timestamp])

        # create a response with the CSV file as an attachment
        response = make_response()
        response.data = open('user_posts.csv', 'rb').read()
        response.headers.set('Content-Disposition', 'attachment', filename='user_posts.csv')
        response.headers.set('Content-Type', 'text/csv')

        # return the response to trigger automatic download
        return response
class Follow(Resource):
    def post(self, username):
        print('hihihihi')
        try:
            to_user = User.get(User.username**username)
        except DoesNotExist:
            return {'message': 'Invalid username'}, 401
        else:
            try:
                Relationship.create(
                    from_user=request.json.get("from_user"),
                    to_user=to_user
                )
            except IntegrityError:
                pass
            else:
                return {'message': f'You are now following {to_user.username}!'}, 201

class Unfollow(Resource):
    def post(self, username):
        try:
            to_user = User.get(User.username**username)
        except DoesNotExist:
            return {'message': 'Invalid action'}, 401
        else:
            try:
                Relationship.get(
                    from_user=request.json.get("from_user"),
                    to_user=to_user
                ).delete_instance()
            except IntegrityError:
                pass
            else:
                return {'message': f'Unfollowed {to_user.username}'}, 201

class Following(Resource):
    def get(self, username):
        print("hihihihih")
        try:
            user = User.get(User.username**username)
        except DoesNotExist:
            return {'message': 'User not found'}, 404
        else:
            following = User.select().join(Relationship, on=Relationship.to_user).where(Relationship.from_user == user)
            following_usernames = [followed_user.username for followed_user in following]
            return {'following': following_usernames}, 200

# Add the Register and Login resources to the API
api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(AddPost, '/posts')
api.add_resource(DeletePost, '/deletepost/<int:post_id>')
api.add_resource(Feed, '/feed')
api.add_resource(Search, '/search')
api.add_resource(EditPost, '/edit')
api.add_resource(DownloadPosts, '/downloadposts/<string:username>')
api.add_resource(Profile,'/profile/<string:username>')
api.add_resource(Follow, '/follow/<string:username>')
api.add_resource(Unfollow, '/unfollow/<string:username>')
api.add_resource(Following, '/following/<string:username>')

if __name__ == '__main__':
    app.run(debug=True)