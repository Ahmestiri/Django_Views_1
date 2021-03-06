from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import User, Room, Topic, Message
from .forms import RegisterForm, RoomForm, UserForm

"""
Authentication
"""

# --- Login --- #


def login_index(request):
    # Variable for login/register
    page = 'login'
    # Redirect if logged in
    if request.user.is_authenticated:
        return redirect('home_index')
    # Login
    if request.method == 'POST':
        # Get form values
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        # User Existance
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')
        # Case user exist
        user = authenticate(request, email=email, password=password)
        # Credentials Testing
        if user is not None:
            login(request, user)
            return redirect('home_index')
        else:
            messages.error(request, 'User does not meet credentials')
    # Response
    response = {'page': page}
    return render(request, "app/Authentication/auth.html", response)


# --- Logout --- #


def logout_index(request):
    logout(request)
    return redirect('home_index')


# --- Register --- #


def register_index(request):
    # Built In Django Form
    form = RegisterForm()
    # Data Processing
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home_index')
        else:
            messages.error(request, 'Error occured during registration')
    # Response
    response = {'form': form}
    return render(request, "app/Authentication/auth.html", response)


"""
User Model
"""

# --- Index --- #


def user_index(request):
    usersArray = []
    rooms = []
    room_messages = []
    # Get all Users
    users = User.objects.all()
    for user in users:
        usersArray.append(user)
        # Get User Rooms
        rooms.append(len(user.room_set.all()))
        # Get User Messages
        room_messages.append(len(user.message_set.all()))
        response = {
            'users': usersArray,
            'rooms': rooms,
            'room_messages': room_messages,
        }
    return render(request, "app/User/index.html", response)


# --- View --- #


def user_view(request, pk):
    # Get all Topics
    topics = Topic.objects.all()
    # Get User by id
    user = User.objects.get(id=pk)
    # Get User Rooms
    rooms = user.room_set.all()
    # Get User Messages
    room_messages = user.message_set.all()
    # Response
    response = {
        'user': user,
        'topics': topics,
        'rooms': rooms,
        'room_messages': room_messages
    }
    return render(request, "app/User/view.html", response)


# --- Edit --- #

@ login_required(login_url='login')
def user_edit(request, pk):
    # Edit User
    form = UserForm(instance=request.user)
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("user_view", pk=request.user.id)
    # Response
    response = {"form": form}
    return render(request, "app/User/edit.html", response)


"""
Room Model
"""

# --- Index --- #


def home_index(request):
    # Get Topics
    topics = Topic.objects.all()
    # Get Rooms by Filter
    q = request.GET.get("q") if request.GET.get("q") != None else ""
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    # Get Messages by Filter
    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q)
    )
    # Response
    response = {
        "topics": topics,
        "rooms": rooms,
        "room_messages": room_messages,
        "total_room_messages": room_messages.count(),
    }
    return render(request, "app/index.html", response)


# --- Add --- #


@ login_required(login_url='login')
def room_add(request):
    # Get Topic
    topics = Topic.objects.all()
    # Create Room
    form = RoomForm()
    if request.method == "POST":
        # Get Form data
        form = RoomForm(request.POST)
        # Get and Create Topic
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        # Create Room
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect("home_index")
    # Reponse
    response = {"form": form, "topics": topics}
    return render(request, "app/Room/add.html", response)


# --- View --- #


def room_view(request, pk):
    # Get Room by id
    room = Room.objects.get(id=pk)
    # Get Messages
    room_messages = room.message_set.all()
    # Get Participants
    participants = room.participants.all()
    # Create Message and Add Participant
    if request.method == "POST":
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room_view', pk=room.id)
    # Response
    response = {
        "room": room,
        "room_messages": room_messages,
        "participants": participants
    }
    return render(request, "app/Room/view.html", response)


# --- Edit --- #


@ login_required(login_url='login')
def room_edit(request, pk):
    # Get Room by id
    room = Room.objects.get(id=pk)
    # Room Creator Only
    if request.user != room.host:
        return HttpResponse("You can't update this room")
    # Edit Room
    form = RoomForm(instance=room)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect("home_index")
    # Response
    response = {"form": form}
    return render(request, "app/Room/edit.html", response)


# --- Delete --- #


@ login_required(login_url='login')
def room_delete(request, pk):
    # Get Room by id
    room = Room.objects.get(id=pk)
    # Room Creator Only
    if request.user != room.host:
        return HttpResponse("You can't delete this room")
    # Delete Room
    if request.method == "POST":
        room.delete()
        return redirect("home_index")
    # Response
    response = {"object": room}
    return render(request, "app/delete.html", response)


"""
Message Model
"""

# --- Delete --- #


@ login_required(login_url='login')
def message_delete(request, pk):
    # Get Message by id
    message = Message.objects.get(id=pk)
    # Message Creator Only
    if request.user != message.user:
        return HttpResponse("You can't delete this message")
    # Delete Message
    if request.method == "POST":
        message.delete()
        return redirect("home_index")
    # Response
    response = {"object": message}
    return render(request, "app/delete.html", response)
