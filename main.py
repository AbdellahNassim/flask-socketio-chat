from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from flask_socketio import join_room, leave_room, SocketIO, send
import json
import random
from string import ascii_uppercase, digits
import datetime
from rooms import generate_random_room_code
from rooms import rooms

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

socketio = SocketIO(app)

def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

@app.route("/",methods=["GET","POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("room_code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        if not name:
            flash("Please enter a name")
            return render_template("home.html")
        if join is not False and not code:
            flash("Please enter a code")
            return render_template("home.html",name=name, code=code)
        room = code 
        if create is not False:
            room = generate_random_room_code()
            # rooms[room] = {
            #     "members": [],
            #     "messages": []
            # }
            conn = get_db_connection()
            conn.execute("INSERT INTO rooms (code) VALUES (?)", (room,))
            conn.commit()
            conn.close()
            
            
        elif room not in rooms:
            flash("Room does not exist")
            return render_template("home.html",name=name,code=code)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    conn = get_db_connection()
    rooms =conn.execute("SELECT * FROM rooms").fetchall()
    rooms = [room["code"] for room in rooms]
    conn.close()
    return render_template("home.html",rooms = rooms)

@app.route("/room",methods=["GET","POST"])
def room():
    print("Hello world")
    room_code = request.args.get("code",None)
    name = request.args.get("name",None)
    print("Room code: ",room_code)
    print("Name: ",name)
    if room_code:
        session["room"] = room_code
    if name:
        session["name"] = name
    if "room" not in session or "name" not in session:
        flash("Please enter a name and a room code")
        return redirect(url_for("home"))
    room = session["room"]
    name = session["name"]
    conn = get_db_connection()
    rooms = conn.execute("SELECT * FROM rooms WHERE code = ?", (room,)).fetchall()
    print("Rooms: ",rooms)
    if len(rooms) == 0:
        return redirect(url_for("home"))
    # if request.method == "POST":
    #     message = request.form.get("message")
    #     if message:
    #         rooms[room]["messages"].append({
    #             "name": name,
    #             "message": message,
    #             "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         })
    #         socketio.emit("message", {
    #             "name": name,
    #             "message": message,
    #             "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         }, room=room)    
    messages = conn.execute("SELECT * FROM messages WHERE room_code = ?", (room,)).fetchall()
    print("Messages: ", messages)
    messages = [{"name": message["sender_name"], "message": message["message"], "time": message["created_at"]} for message in messages]
    members = conn.execute("SELECT * FROM members WHERE room_code = ?", (room,)).fetchall()
    members = [member["name"] for member in members]
    conn.close()
    return render_template("room.html", room=room, name=name,messages=messages,members=members)


@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return redirect(url_for("home"))
    conn = get_db_connection()
    rooms = conn.execute("SELECT * FROM rooms WHERE code = ?", (room,)).fetchall()
    if len(rooms) == 0:
        leave_room(room)
        return redirect(url_for("home"))
    
    join_room(room)
    conn.execute("INSERT INTO members (room_code, name) VALUES (?, ?)", (room, name))
    conn.commit()
    conn.close()
    data =  {
        "data" : {"name" : name, "message" : "has entered the room.", 
          "time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          }
    }
    send(json.dumps(data),to=room,broadcast=True)
    print(f"{name} has connected to {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return redirect(url_for("home"))
    conn = get_db_connection()
    rooms = conn.execute("SELECT * FROM rooms WHERE code = ?", (room,)).fetchall()
    if len(rooms) == 0:
        leave_room(room)
        return redirect(url_for("home"))
    leave_room(room)
    conn.execute("DELETE FROM members WHERE room_code = ? AND name = ?", (room, name))
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM members WHERE room_code = ?", (room,)).fetchone()[0]
    if count == 0:
        conn.execute("DELETE FROM rooms WHERE code = ?", (room,))
        conn.commit()
    data = {
        "data" : {"name" : name, "message" : "has left the room.",
            "time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
                  }
    }
    conn.close()
    send(json.dumps(data),to=room,broadcast=True)
    print(f"{name} has disconnected from {room}")
@socketio.on("send message")
def send_message(message):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return redirect(url_for("home"))
    conn = get_db_connection()
    rooms = conn.execute("SELECT * FROM rooms WHERE code = ?", (room,)).fetchall()
    if len(rooms) == 0:
        leave_room(room)
        return redirect(url_for("home"))
    conn.execute("INSERT INTO messages (room_code, sender_name, message) VALUES (?, ?, ?)", (room, name, message["data"]["message"]))
    conn.commit()
    # rooms[room]["messages"].append({
    #     "name": name,
    #     "message": message["data"]["message"],
    #     "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # })
    socketio.emit("receive message", {
        "name": name,
        "message": message["data"]["message"],
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, room=room)
if __name__ == "__main__":

    socketio.run(app, debug=True)