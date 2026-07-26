from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "community-kitchen-secret-key"

DATABASE = "database.db"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            meals_served INTEGER NOT NULL,
            rice_kg REAL NOT NULL,
            dal_kg REAL NOT NULL,
            vegetables_kg REAL NOT NULL,
            stock_balance REAL NOT NULL,
            cost_per_meal REAL NOT NULL
        )
    """)

    conn.commit()

    # Add sample records only if database is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM records"
    ).fetchone()[0]

    if count == 0:

        sample_data = [

            ("2026-07-01", 120, 18, 6, 12, 95, 1.50),
            ("2026-07-02", 135, 20, 7, 14, 90, 1.45),
            ("2026-07-03", 110, 17, 5, 11, 84, 1.55),
            ("2026-07-04", 150, 23, 8, 15, 78, 1.40),
            ("2026-07-05", 145, 22, 7, 14, 72, 1.42),
            ("2026-07-06", 160, 25, 9, 16, 65, 1.38),
            ("2026-07-07", 125, 19, 6, 12, 60, 1.48),
            ("2026-07-08", 140, 21, 7, 13, 55, 1.44),
            ("2026-07-09", 155, 24, 8, 15, 48, 1.39),
            ("2026-07-10", 130, 20, 6, 12, 43, 1.46),
            ("2026-07-11", 170, 26, 9, 17, 37, 1.35),
            ("2026-07-12", 165, 25, 8, 16, 31, 1.37),
            ("2026-07-13", 145, 22, 7, 14, 26, 1.43),
            ("2026-07-14", 180, 28, 10, 18, 20, 1.32),
            ("2026-07-15", 150, 23, 8, 15, 15, 1.41),
            ("2026-07-16", 135, 20, 7, 13, 10, 1.47),
            ("2026-07-17", 125, 19, 6, 12, 8, 1.50),
            ("2026-07-18", 160, 24, 8, 16, 5, 1.39),
            ("2026-07-19", 140, 21, 7, 14, 3, 1.45),
            ("2026-07-20", 155, 23, 8, 15, 1, 1.42)

        ]

        conn.executemany("""
            INSERT INTO records
            (
                date,
                meals_served,
                rice_kg,
                dal_kg,
                vegetables_kg,
                stock_balance,
                cost_per_meal
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_data)

        conn.commit()

    conn.close()


# =====================================================
# HOME / DASHBOARD
# =====================================================

@app.route("/")
def index():

    search = request.args.get("search", "").strip()
    stock_filter = request.args.get("stock", "")

    conn = get_db()

    # -----------------------------------------------
    # Get filtered records
    # -----------------------------------------------

    query = """
        SELECT *
        FROM records
        WHERE 1=1
    """

    params = []

    # Search by ID or Date
    if search:

        query += """
            AND (
                CAST(record_id AS TEXT) LIKE ?
                OR date LIKE ?
            )
        """

        params.extend([
            f"%{search}%",
            f"%{search}%"
        ])

    # Low stock filter
    if stock_filter == "low":

        query += """
            AND stock_balance < 10
        """

    # Latest records first
    query += """
        ORDER BY date DESC, record_id DESC
    """

    records = conn.execute(
        query,
        params
    ).fetchall()


    # -----------------------------------------------
    # Total meals served
    # -----------------------------------------------

    total_meals = conn.execute("""
        SELECT COALESCE(SUM(meals_served), 0)
        FROM records
    """).fetchone()[0]


    # -----------------------------------------------
    # Low stock records
    # -----------------------------------------------

    low_stock = conn.execute("""
        SELECT COUNT(*)
        FROM records
        WHERE stock_balance < 10
    """).fetchone()[0]


    # -----------------------------------------------
    # Total records
    # IMPORTANT:
    # This counts ALL records, not filtered records
    # -----------------------------------------------

    total_records = conn.execute("""
        SELECT COUNT(*)
        FROM records
    """).fetchone()[0]


    conn.close()


    return render_template(
        "index.html",

        records=records,

        total_meals=total_meals,

        low_stock=low_stock,

        total_records=total_records,

        search=search,

        stock_filter=stock_filter
    )


# =====================================================
# ADD RECORD
# =====================================================

@app.route("/add", methods=["GET", "POST"])
def add_record():

    if request.method == "POST":

        try:

            date = request.form["date"]

            meals_served = int(
                request.form["meals_served"]
            )

            rice_kg = float(
                request.form["rice_kg"]
            )

            dal_kg = float(
                request.form["dal_kg"]
            )

            vegetables_kg = float(
                request.form["vegetables_kg"]
            )

            stock_balance = float(
                request.form["stock_balance"]
            )

            cost_per_meal = float(
                request.form["cost_per_meal"]
            )


            # Validate date
            datetime.strptime(
                date,
                "%Y-%m-%d"
            )


            # Validate meals
            if meals_served <= 0:

                raise ValueError(
                    "Meals served must be greater than 0."
                )


            # Validate ration
            if (
                rice_kg < 0
                or dal_kg < 0
                or vegetables_kg < 0
            ):

                raise ValueError(
                    "Ration values cannot be negative."
                )


            # Validate stock
            if stock_balance < 0:

                raise ValueError(
                    "Stock balance cannot be negative."
                )


            # Validate cost
            if cost_per_meal < 0:

                raise ValueError(
                    "Cost cannot be negative."
                )


            conn = get_db()


            conn.execute("""
                INSERT INTO records
                (
                    date,
                    meals_served,
                    rice_kg,
                    dal_kg,
                    vegetables_kg,
                    stock_balance,
                    cost_per_meal
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (

                date,
                meals_served,
                rice_kg,
                dal_kg,
                vegetables_kg,
                stock_balance,
                cost_per_meal

            ))


            conn.commit()

            conn.close()


            flash(
                "Record added successfully!",
                "success"
            )


            return redirect(
                url_for("index")
            )


        except ValueError as e:

            flash(
                f"Invalid data: {e}",
                "error"
            )


        except Exception:

            flash(
                "Something went wrong while saving the record.",
                "error"
            )


    return render_template(
        "add.html"
    )


# =====================================================
# EDIT RECORD
# =====================================================

@app.route(
    "/edit/<int:record_id>",
    methods=["GET", "POST"]
)
def edit_record(record_id):

    conn = get_db()


    record = conn.execute(
        """
        SELECT *
        FROM records
        WHERE record_id = ?
        """,
        (record_id,)
    ).fetchone()


    # Record not found
    if record is None:

        conn.close()

        flash(
            "Record not found.",
            "error"
        )

        return redirect(
            url_for("index")
        )


    if request.method == "POST":

        try:

            date = request.form["date"]

            meals_served = int(
                request.form["meals_served"]
            )

            rice_kg = float(
                request.form["rice_kg"]
            )

            dal_kg = float(
                request.form["dal_kg"]
            )

            vegetables_kg = float(
                request.form["vegetables_kg"]
            )

            stock_balance = float(
                request.form["stock_balance"]
            )

            cost_per_meal = float(
                request.form["cost_per_meal"]
            )


            # Validate date
            datetime.strptime(
                date,
                "%Y-%m-%d"
            )


            if meals_served <= 0:

                raise ValueError(
                    "Meals served must be greater than 0."
                )


            if (
                rice_kg < 0
                or dal_kg < 0
                or vegetables_kg < 0
            ):

                raise ValueError(
                    "Ration values cannot be negative."
                )


            if stock_balance < 0:

                raise ValueError(
                    "Stock balance cannot be negative."
                )


            if cost_per_meal < 0:

                raise ValueError(
                    "Cost cannot be negative."
                )


            conn.execute("""
                UPDATE records

                SET
                    date = ?,
                    meals_served = ?,
                    rice_kg = ?,
                    dal_kg = ?,
                    vegetables_kg = ?,
                    stock_balance = ?,
                    cost_per_meal = ?

                WHERE record_id = ?

            """, (

                date,
                meals_served,
                rice_kg,
                dal_kg,
                vegetables_kg,
                stock_balance,
                cost_per_meal,
                record_id

            ))


            conn.commit()

            conn.close()


            flash(
                "Record updated successfully!",
                "success"
            )


            return redirect(
                url_for("index")
            )


        except ValueError as e:

            flash(
                f"Invalid data: {e}",
                "error"
            )


        except Exception:

            flash(
                "Something went wrong while updating.",
                "error"
            )


    conn.close()


    return render_template(
        "edit.html",
        record=record
    )


# =====================================================
# DELETE RECORD
# =====================================================

@app.route(
    "/delete/<int:record_id>",
    methods=["POST"]
)
def delete_record(record_id):

    conn = get_db()


    # Check whether record exists
    record = conn.execute(
        """
        SELECT *
        FROM records
        WHERE record_id = ?
        """,
        (record_id,)
    ).fetchone()


    if record is None:

        conn.close()

        flash(
            "Record not found.",
            "error"
        )

        return redirect(
            url_for("index")
        )


    # Delete record
    conn.execute(
        """
        DELETE FROM records
        WHERE record_id = ?
        """,
        (record_id,)
    )


    conn.commit()

    conn.close()


    flash(
        "Record deleted successfully.",
        "success"
    )


    return redirect(
        url_for("index")
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )