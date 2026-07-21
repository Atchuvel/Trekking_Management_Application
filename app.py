from flask import Flask, render_template, request, redirect,session
from flask_sqlalchemy import SQLAlchemy
from models.extensions import db
from datetime import datetime, date
from models.models import User, Trek, Booking

app = Flask(__name__)
app.secret_key = "trekking_management_secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trekking.db"


db.init_app(app)
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        name = request.form["name"]
        contact = request.form["contact"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return """
                <script>
                alert("Username already exists!");
                window.history.back();
                </script>
                """

        if password != confirm_password:
            return """
                <script>
                alert("Passwords do not match");
                window.history.back();
                </script>
                """

        else:
            new_user = User(
                username=username,
                name=name,
                contact=contact,
                password=password,
                role=role,
                status = "Approved" if role == "user" else "Pending"
            )

        db.session.add(new_user)
        db.session.commit()

        return """
        <script>
        alert("Registration Successful");
        window.location.href="/login";
        </script>
        """

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():


    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:

            # Save login details
            session["user_id"] = user.id
            session["username"] = user.username
            session["name"] = user.name
            session["role"] = user.role

            if user.role == "admin":
                return redirect("/admin")

            elif user.role == "user":
                return redirect("/user")

            elif user.role == "staff":

                if user.status == "Approved":
                    return redirect("/staff")

                elif user.status == "Pending":
                    return """
                        <script>
                        alert("Waiting for Admin Approval");
                        window.location.href="/login";
                        </script>
                        """

                elif user.status == "Blacklisted":
                    return """
                        <script>
                        alert("Your account has been blacklisted.");
                        window.location.href="/login";
                        </script>
                        """

        else:
            return """
                <script>
                alert("Invalid Username or Password");
                window.location.href="/login";
                </script>
                """

    return render_template("login.html")

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    user = db.session.get(User, session["user_id"])

    if request.method == "POST":

        user.name = request.form["name"]

        user.contact = request.form["contact"]

        password = request.form["password"]

        confirm = request.form["confirm_password"]

        if password:

            if password != confirm:

                return """
                <script>
                alert("Passwords do not match.");
                window.location="/edit_profile";
                </script>
                """

            user.password = password

        db.session.commit()

        return """
        <script>
        alert("Profile updated successfully.");
        window.location="/edit_profile";
        </script>
        """

    return render_template(
        "/edit_profile.html",
        user=user
    )



@app.route("/treks")
def treks():

    update_trek_status()

    trek_list = Trek.query.all()

    trek_details = []

    for trek in trek_list:

        bookings = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        trek_details.append({
            "trek": trek,
            "bookings": bookings
        })

    return render_template(
        "treks.html",
        trek_details=trek_details
    )

@app.route("/add_trek", methods=["GET", "POST"])
def add_trek():
    
    if request.method == "POST":

        trek_name = request.form["trek_name"]
        location = request.form["location"]
        difficulty = request.form["difficulty"]
        start_date = request.form["start_date"]
        duration = request.form["duration"]
        price = request.form["price"]
        available_slots = request.form["available_slots"]

        new_trek = Trek(
            trek_name=trek_name,
            location=location,
            difficulty=difficulty,
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            duration=int(duration),
            price=float(price),
            available_slots=int(available_slots)
        )

        db.session.add(new_trek)
        db.session.commit()


        return """
            <script>
            alert("Trek Added Successfully");
            window.history.back();
            </script>
            """

    return render_template("admin/add_trek.html")

@app.route("/admin")
def admin():

    update_trek_status()

    # Trek Details
    total_treks = Trek.query.count()

    open_treks = Trek.query.filter_by(status="Open").count()

    full_treks = Trek.query.filter_by(status="Full").count()

    completed_treks = Trek.query.filter_by(status="Completed").count()

    cancelled_treks = Trek.query.filter_by(status="Cancelled").count()

    # Trekker Details
    total_trekkers = User.query.filter_by(role="user").count()

    # Staff Details
    total_staff = User.query.filter_by(
        role="staff"
        ).count()

    approved_staff = User.query.filter_by(
        role="staff",
        status="Approved"
        ).count()

    pending_staff = User.query.filter_by(
        role="staff",
        status="Pending"
        ).count()

    blacklisted_staff = User.query.filter_by(
        role="staff",
        status ="Blacklisted"
        ).count()

    # Assigned Staff
    assigned_staff = len({
        trek.assigned_staff
        for trek in Trek.query.filter(Trek.assigned_staff != None).all()
    })

    # Available Staff (Approved but not assigned)
    available_staff = approved_staff - assigned_staff

    # Booking Details
    total_bookings = Booking.query.count()

    cancelled_bookings = Booking.query.filter_by(
        status="Cancelled"
    ).count()

    return render_template(
        "admin/admin_dashboard.html",

        total_treks=total_treks,
        open_treks=open_treks,
        full_treks=full_treks,
        completed_treks=completed_treks,
        cancelled_treks=cancelled_treks,

        total_trekkers=total_trekkers,

        total_staff=total_staff,
        assigned_staff=assigned_staff,
        available_staff=available_staff,
        pending_staff=pending_staff,
        blacklisted_staff=blacklisted_staff,

        total_bookings=total_bookings,
        cancelled_bookings=cancelled_bookings,
    )

@app.route("/view_treks")
def view_treks():

    update_trek_status()

    unassigned_treks = Trek.query.filter_by(assigned_staff=None).all()

    assigned_treks = Trek.query.filter(Trek.assigned_staff != None).all()

    return render_template(
        "admin/view_treks.html",
        unassigned_treks=unassigned_treks,
        assigned_treks=assigned_treks,
        User=User,
        Booking=Booking
)

@app.route("/edit_trek/<int:id>", methods=["GET", "POST"])
def edit_trek(id):

    update_trek_status()

    trek = db.session.get(Trek, id)

    staff = User.query.filter_by(
        role="staff",
        status="Approved"
    ).all()

    if request.method == "POST":

        # Prevent reducing slots below booked participants
        booked_count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        new_slots = int(request.form["available_slots"])

        if new_slots < booked_count:
            return """
            <script>
            alert("Total slots cannot be less than the current booked participants.");
            window.history.back();
            </script>
            """

        trek.trek_name = request.form["trek_name"]

        trek.location = request.form["location"]

        trek.difficulty = request.form["difficulty"]

        trek.start_date = datetime.strptime(
            request.form["start_date"],
            "%Y-%m-%d"
        ).date()

        trek.duration = int(request.form["duration"])

        trek.price = float(request.form["price"])

        trek.available_slots = new_slots

        trek.assigned_staff = (
            int(request.form["assigned_staff"])
            if request.form["assigned_staff"]
            else None
        )

        trek.status = request.form["status"]

        db.session.commit()

        return redirect("/view_treks")

    return render_template(
        "admin/edit_trek.html",
        trek=trek,
        staff=staff
    )

@app.route("/update_trekker_status/<int:id>", methods=["POST"])
def update_trekker_status(id):

    trekker =  db.session.get(User,id)

    if trekker is None or trekker.role != "user":
        return "User not found"

    trekker.status = request.form["status"]

    db.session.commit()

    return """
    <script>
    alert("Trekker status updated successfully!");
    window.location.href="/view_trekkers";
    </script>
    """

@app.route("/delete_trek/<int:id>")
def delete_trek(id):

    trek = Trek.query.get_or_404(id)

    booking_count = Booking.query.filter_by(
        trek_id=id
    ).count()

    if booking_count > 0:
        return """
        <script>
        alert('Cannot delete trek because bookings exist.');
        window.location='/view_treks';
        </script>
        """

    db.session.delete(trek)
    db.session.commit()

    return """
    <script>
    alert('Trek deleted successfully.');
    window.location='/view_treks';
    </script>
    """


def update_trek_status():

    treks = Trek.query.all()

    today = date.today()

    for trek in treks:

        # Manual override - never change
        if trek.status == "Cancelled":
            continue

        # Manual Completed OR automatic after date
        if trek.status == "Completed":
            continue

        if trek.start_date < today:
            trek.status = "Completed"
            continue

        # Count active bookings
        bookings = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        # Automatic Open / Full
        if bookings >= trek.available_slots:
            trek.status = "Full"
        else:
            trek.status = "Open"

    db.session.commit()

    
@app.route("/view_trekkers")
def view_trekkers():

    trekkers = User.query.filter_by(role="user").all()

    trekker_details = []

    for trekker in trekkers:

        bookings = Booking.query.filter_by(
            user_id=trekker.id,
            status="Booked"
        ).all()

        total_bookings = len(bookings)

        total_amount = 0

        for booking in bookings:

            trek = db.session.get(Trek, booking.trek_id)

            if trek:
                total_amount += trek.price

        trekker_details.append({
            "user": trekker,
            "bookings": total_bookings,
            "amount": total_amount
        })

    return render_template(
        "admin/view_trekkers.html",
        trekker_details=trekker_details
    )

@app.route("/admin/search")
def admin_search():

    search = request.args.get("search", "").strip()

    if search == "":
        return redirect("/admin")

    # Search Trek
    trek = Trek.query.filter(
        Trek.trek_name.ilike(f"%{search}%")
    ).first()

    if trek:
        return redirect(f"/view_treks?search={search}")

    # Search Staff
    staff = User.query.filter_by(role="staff").filter(
        User.username.ilike(f"%{search}%")
    ).first()

    if staff:
        return redirect(f"/manage_staff?search={search}")

    # Search Trekker
    trekker = User.query.filter_by(role="user").filter(
        User.username.ilike(f"%{search}%")
    ).first()

    if trekker:
        return redirect(f"/view_trekkers?search={search}")

    return """
    <script>
    alert("No matching record found.");
    window.history.back();
    </script>
    """


@app.route("/view_bookings/<int:id>")
def view_bookings(id):

    trek = db.session.get(Trek, id)

    bookings = Booking.query.filter_by(
        trek_id=id
    ).all()

    return render_template(
        "admin/view_bookings.html",
        trek=trek,
        bookings=bookings,
        User=User
    )


@app.route("/logout")
def logout():

    update_trek_status()

    session.clear()

    return redirect("/")

@app.route("/manage_staff")
def manage_staff():

    staff = User.query.filter_by(role="staff").all()

    staff_details = []

    for user in staff:

        completed_treks=Trek.query.filter_by(
            assigned_staff=user.id,
            status="Completed"
        ).count()
        


        assigned_treks = Trek.query.filter_by(
            assigned_staff=user.id
        ).count()



        staff_details.append({
            "user": user,
            "assigned_treks": assigned_treks,
            "completed_treks": completed_treks
        })

    return render_template(
        "admin/manage_staff.html",
        staff_details=staff_details
    )

@app.route("/update_staff_status/<int:id>", methods=["POST"])


def update_staff_status(id):

    staff = db.session.get(User,id)

    if staff is None:
        return "Staff not found"

    staff.status = request.form["status"]

    db.session.commit()

    return """
    <script>
    alert("Staff status updated successfully!");
    window.location.href="/manage_staff";
    </script>
    """



@app.route("/staff")
def staff_dashboard():

    update_trek_status()

    staff_id = session["user_id"]

    # Total treks in the system
    total_treks = Trek.query.count()

    # Treks assigned to this staff member
    my_treks = Trek.query.filter_by(
        assigned_staff=staff_id
    ).count()

    # Open treks assigned to this staff member
    open_treks = Trek.query.filter_by(
        assigned_staff=staff_id,
        status="Open"
    ).count()

    # Completed treks assigned to this staff member
    completed_treks = Trek.query.filter_by(
        assigned_staff=staff_id,
        status="Completed"
    ).count()

    return render_template(
        "staff/staff_dashboard.html",
        total_treks=total_treks,
        my_treks=my_treks,
        open_treks=open_treks,
        completed_treks=completed_treks
    )

@app.route("/staff/view_treks")
def staff_view_treks():
    update_trek_status()

    treks = Trek.query.all()

    return render_template(
        "staff/view_treks.html",
        treks=treks
    )

@app.route("/staff/assigned_treks")
def assigned_treks():

    update_trek_status()

    staff = db.session.get(User, session["user_id"])

    treks = Trek.query.filter_by(
        assigned_staff=staff.id
    ).all()

    trek_details = []

    for trek in treks:

        participants = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        trek_details.append({
            "trek": trek,
            "participants": participants
        })

    return render_template(
        "staff/assigned_treks.html",
        trek_details=trek_details
    )

@app.route("/staff/edit_trek/<int:id>", methods=["GET", "POST"])
def staff_edit_trek(id):

    update_trek_status()

    trek = db.session.get(Trek,id)

    if trek is None:
        return "Trek not found"

    if request.method == "POST":

        booked_count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        new_slots = int(request.form["available_slots"])

        if new_slots < booked_count:
            return """
            <script>
            alert("Total slots cannot be less than the current booked participants.");
            window.history.back();
            </script>
            """

        trek.available_slots = new_slots


        trek.available_slots = int(request.form["available_slots"])
        trek.status = request.form["status"]

        db.session.commit()

        return redirect("/staff/assigned_treks")

    return render_template(
        "staff/edit_trek.html",
        trek=trek
    )



@app.route("/staff/view_participants/<int:id>")
def view_participants(id):

    trek = db.session.get(Trek,id)

    bookings = Booking.query.filter_by(
        trek_id=id
    ).all()

    return render_template(
        "staff/view_participants.html",
        trek=trek,
        bookings=bookings,
        User=User
    )

@app.route("/staff/cancel_booking/<int:id>")
def staff_cancel_booking(id):

    booking = db.session.get(Booking,id)

    if booking is None:
        return "Booking not found"

    trek = db.session.get(Trek,booking.trek_id)

    # Only the assigned staff can cancel bookings
    if trek.assigned_staff != session["user_id"]:
        return "Unauthorized"

    # Only booked participants can be cancelled
    if booking.status != "Booked":
        return """
        <script>
        alert("This booking cannot be cancelled.");
        window.history.back();
        </script>
        """

    booking.status = "Cancelled"

    db.session.commit()

    update_trek_status()

    return """
    <script>
    alert("Participant Booking Cancelled Successfully!");
    window.history.back();
    </script>
    """

@app.route("/user")
def user_dashboard():

    update_trek_status()

    user_id = session["user_id"]

    total_treks = Trek.query.filter_by(status="Open").count()

    my_bookings = Booking.query.join(
        Trek,
        Booking.trek_id == Trek.id
    ).filter(
        Booking.user_id==user_id,
        Booking.status=="Booked",
        Trek.status != "Completed"
    ).count()

    completed_treks = Booking.query.join(
        Trek,
        Booking.trek_id == Trek.id
    ).filter(
        Booking.user_id == user_id,
        Trek.status == "Completed"
    ).count()

    Cancelled_treks = Booking.query.filter_by(
    user_id=user_id,
    status="Cancelled").count()

    return render_template(
        "user/user_dashboard.html",
        total_treks=total_treks,
        my_bookings=my_bookings,
        completed_treks=completed_treks,
        Cancelled_treks=Cancelled_treks
    )

@app.route("/user/view_treks")
def user_view_treks():

    update_trek_status()

    treks = Trek.query

    # Get search values
    location = request.args.get("location", "").strip()
    difficulty = request.args.get("difficulty", "")
    condition = request.args.get("condition", "")
    duration = request.args.get("duration", "")

    # Location Filter
    if location:
        treks = treks.filter(
            Trek.location.ilike(f"%{location}%")
        )

    # Difficulty Filter
    if difficulty:
        treks = treks.filter_by(
            difficulty=difficulty
        )

    # Duration Filter
    if duration:

        duration = int(duration)

        if condition == ">":
            treks = treks.filter(Trek.duration > duration)

        elif condition == "<":
            treks = treks.filter(Trek.duration < duration)

        elif condition == "=":
            treks = treks.filter(Trek.duration == duration)

    treks = treks.all()

    other_treks = sum(
        1 for trek in treks
        if trek.status != "Open"
    )

    return render_template(
        "user/view_treks.html",
        treks=treks,
        other_treks=other_treks
    )


@app.route("/user/book_trek/<int:id>", methods=["GET", "POST"])
def book_trek(id):

    update_trek_status()

    trek = db.session.get(Trek,id)

    if trek is None:
        return "Trek not found"

    staff = None

    if trek.assigned_staff:
        staff = db.session.get(User,trek.assigned_staff)

    current_bookings = Booking.query.filter_by(
        trek_id=trek.id,
        status="Booked"
    ).count()

    if request.method == "POST":

        # Allow booking only if trek is Open
        if trek.status != "Open":
            return "This trek is not available for booking."

        # Stop booking if slots are already full
        if current_bookings >= trek.available_slots:

            trek.status = "Full"
            db.session.commit()

            return "This trek is full."

        # Prevent duplicate booking
        existing_booking = Booking.query.filter_by(
            user_id=session["user_id"],
            trek_id=trek.id
        ).first()

        if existing_booking:
            return  """
                <script>
                alert("You have already booked this trek before.");
                window.location.href="/user/view_treks";
                </script>
                """

        # Save booking
        booking = Booking(
            user_id=session["user_id"],
            trek_id=trek.id
        )

        db.session.add(booking)
        db.session.commit()

        # Check again after booking
        current_bookings = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()

        if current_bookings >= trek.available_slots:
            trek.status = "Full"
            db.session.commit()
        update_trek_status()
        return redirect("/user/my_bookings")

    return render_template(
        "user/book_trek.html",
        trek=trek,
        staff=staff,
        current_bookings=current_bookings
    )



@app.route("/user/my_bookings")
def my_bookings():

    update_trek_status()

    location = request.args.get("location", "").strip()

    bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    booking_details = []

    for booking in bookings:

        trek = db.session.get(Trek,booking.trek_id)

        # Location Search
        if location:
            if location.lower() not in trek.location.lower():
                continue

        booking_details.append({
            "booking": booking,
            "trek": trek
        })

    return render_template(
        "user/my_bookings.html",
        booking_details=booking_details
    )

@app.route("/user/cancel_booking/<int:id>")
def cancel_booking(id):

    booking = db.session.get(Booking,id)

    if booking is None:
        return "Booking not found"

    if booking.user_id != session["user_id"]:
        return "Unauthorized"

    trek = db.session.get(Trek,booking.trek_id)

    if trek.status == "Completed":
        return """
        <script>
        alert("Completed trek bookings cannot be cancelled.");
        window.location.href="/user/my_bookings";
        </script>
        """

    if booking.status != "Booked":
        return "Booking already cancelled or completed"

    booking.status = "Cancelled"

    db.session.commit()

    return """
    <script>
    alert("Booking Cancelled Successfully!");
    window.location.href="/user/my_bookings";
    </script>
    """


with app.app_context():
    db.create_all()

    if User.query.filter_by(username="admin").first() is None:
        admin = User(
            username="admin",
            name="Administrator",
            contact="9999999999",
            password="1234",
            role="admin",
            status="Approved"
            )

        db.session.add(admin)
        db.session.commit()

        print("Admin user created")
if __name__ == "__main__":
    app.run(debug=True)
