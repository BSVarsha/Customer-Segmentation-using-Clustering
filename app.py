from flask import Flask, render_template, request, redirect, session
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = "secret123"   # required for session

# ---------------- LOAD MODEL ---------------- #

try:
    with open("kmeans_model.pkl", "rb") as f:
        model = pickle.load(f)

    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)

    print("Model loaded successfully")

except Exception as e:
    print("Error loading model:", e)

# ---------------- USER STORAGE ---------------- #
users = {}

# ---------------- ROUTES ---------------- #

# Login page
@app.route('/')
def login_page():
    return render_template('login.html')


# Login action
@app.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    pwd = request.form['password']

    if user in users and users[user] == pwd:
        session['user'] = user   # store login session
        return redirect('/dashboard')
    else:
        return "Invalid Login"


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        users[user] = pwd
        return redirect('/')

    return render_template('register.html')


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')   # protect page

    return render_template('dashboard.html', user=session['user'])


# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


# Prediction
@app.route('/predict', methods=['POST'])
def predict():
    try:
        age = float(request.form['age'])
        income = float(request.form['income'])
        score = float(request.form['score'])

        # Input Validation: Ensure inputs are within realistic training ranges
        # Training ranges are roughly: Age(18-70), Income(15-137), Score(1-100)
        if income > 1000: # User probably entered full salary instead of k$
            income = income / 1000
        
        if score > 100:
            score = 100
        elif score < 0:
            score = 0

        print(f"DEBUG - Raw Input: Age={age}, Income={income}, Score={score}")

        # Prediction
        data = np.array([[age, income, score]])
        scaled = scaler.transform(data)
        print(f"DEBUG - Scaled Input: {scaled}")

        cluster = int(model.predict(scaled)[0])
        print(f"DEBUG - Raw Cluster Predicted: {cluster}")

        # The cluster labels mapping should match the model's training
        # Most Mall Customer K-Means models use these 5 clusters:
        # 0: Standard (Mid/Mid), 1: Careful (High/Low), 2: Target (High/High), 3: Budget (Low/High), 4: Sensible (Low/Low)
        labels = {
            0: "Standard Customer (Average Income & Spend)",
            1: "Careful Spender (High Income, Conservative Spend)",
            2: "Target Customer (High Income, High Spend)",
            3: "Budget Spender (Low Income, High Spend)",
            4: "Sensible Spender (Low Income, Low Spend)"
        }

        # Fallback if cluster is not in dictionary
        label = labels.get(cluster, "Unknown Segment")
        print(f"DEBUG - Final Label: {label}")

        return render_template(
            'result.html',
            cluster=cluster,
            label=label,
            age=age,
            income=income,
            score=score,
            user=session.get('user')
        )

    except Exception as e:
        print("ERROR:", e)
        return f"Error: {e}"


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    print("Flask app is starting...")
    app.run(debug=True)