import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template_string, request, redirect,
                    url_for, session, flash, abort)
from werkzeug.utils import secure_filename
from PIL import Image

# ============================================================
#  SETTINGS — change these to match your brand
# ============================================================
APP_NAME = "AI Prompts"
IG_HANDLE = "@ai_prompt.s"
IG_URL = "https://instagram.com/ai_prompt.s"
CONTACT_EMAIL = "aiprompt.s26@gmail.com"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "changeme123"   # <-- CHANGE THIS before going live!

# ============================================================
#  BASIC SETUP — you don't need to touch this part
# ============================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DB_PATH = os.path.join(BASE_DIR, "database.db")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-this-with-a-long-random-string"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image TEXT NOT NULL,
            prompt TEXT NOT NULL,
            tool TEXT,
            category TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


init_db()


def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            flash("Please log in.", "error")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


@app.context_processor
def inject_globals():
    return dict(
        APP_NAME=APP_NAME,
        IG_HANDLE=IG_HANDLE,
        IG_URL=IG_URL,
        CONTACT_EMAIL=CONTACT_EMAIL,
        year=datetime.now().year,
    )

# ============================================================
#  ALL THE HTML LIVES HERE (as one shared "layout")
# ============================================================
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}{{ APP_NAME }}{% endblock %}</title>
<link rel="icon" href="{{ url_for('static', filename='logo.png') }}">
<style>
:root{
  --yellow:#FFD400; --yellow-dark:#F0B800;
  --pink:#E1306C; --purple:#833AB4; --orange:#F77737;
  --dark:#111; --gray:#666; --light:#fafafa; --border:#eee;
  --radius:14px; --shadow:0 4px 20px rgba(0,0,0,.06);
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--dark);background:#fff;line-height:1.6}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.nav{display:flex;justify-content:space-between;align-items:center;padding:16px 32px;border-bottom:1px solid var(--border);position:sticky;top:0;background:#fff;z-index:20;flex-wrap:wrap;gap:10px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:20px}
.brand-logo{width:36px;height:36px;object-fit:contain}
.nav nav a{margin-left:20px;font-weight:600;color:var(--gray)}
.nav nav a:hover{color:var(--dark)}
.btn{display:inline-block;background:var(--yellow);color:var(--dark);padding:12px 22px;border-radius:999px;font-weight:700;border:none;cursor:pointer;font-size:15px;transition:.2s}
.btn:hover{background:var(--yellow-dark);transform:translateY(-1px)}
.btn.ghost{background:#fff;border:2px solid var(--dark)}
.btn.ghost:hover{background:var(--dark);color:#fff}
.btn-sm{background:var(--yellow);padding:8px 14px;border-radius:999px;font-size:13px;font-weight:700;border:none;cursor:pointer}
.btn-sm.ghost{background:#fff;border:1.5px solid var(--dark)}
.btn-sm.danger{background:#ff4757;color:#fff}
.flashes{padding:10px 32px}
.flash{padding:10px 16px;border-radius:8px;margin-bottom:8px;font-weight:600}
.flash.success{background:#e8f8ee;color:#1a7a3f}
.flash.error{background:#fdeaea;color:#b02020}
.hero{display:grid;grid-template-columns:1.3fr 1fr;gap:40px;align-items:center;padding:70px 40px;max-width:1200px;margin:0 auto}
.hero h1{font-size:52px;line-height:1.1;margin:0 0 16px}
.hero .accent{background:linear-gradient(90deg,var(--yellow),var(--orange),var(--pink));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{font-size:18px;color:var(--gray)}
.hero .cta{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0 12px}
.hero .small{font-size:14px;color:var(--gray)}
.hero-img img{border-radius:24px;box-shadow:var(--shadow);border:6px solid var(--yellow);width:100%}
.section{max-width:1200px;margin:0 auto;padding:50px 40px}
.section.narrow{max-width:760px}
.section-title{font-size:28px;margin:0 0 24px}
.page-title{font-size:40px;margin:0 0 20px}
.lead{font-size:18px;color:var(--gray)}
.center{text-align:center;margin-top:30px}
.muted{color:var(--gray)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:22px}
.card{background:#fff;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;transition:.25s;display:flex;flex-direction:column}
.card:hover{transform:translateY(-4px);box-shadow:var(--shadow)}
.card img{aspect-ratio:1/1;object-fit:cover;width:100%}
.card-body{padding:14px}
.card .tag{display:inline-block;background:var(--yellow);padding:3px 10px;border-radius:999px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.5px}
.prompt-line{font-size:14px;margin:10px 0;color:#222}
.tool{font-size:12px;color:var(--pink);font-weight:700}
.search{display:flex;gap:10px;margin-bottom:28px;flex-wrap:wrap}
.search input,.search select{padding:12px 16px;border:1.5px solid var(--border);border-radius:999px;font-size:15px;outline:none;flex:1;min-width:180px}
.search input:focus,.search select:focus{border-color:var(--yellow)}
.detail{display:grid;grid-template-columns:1.2fr 1fr;gap:40px;max-width:1200px;margin:0 auto;padding:50px 40px}
.detail-img img{border-radius:var(--radius);box-shadow:var(--shadow)}
.prompt-box{background:var(--light);border:1.5px solid var(--border);border-radius:var(--radius);padding:18px;white-space:pre-wrap;font-family:inherit;font-size:15px;line-height:1.6;margin:10px 0 18px}
.detail-info .btn{margin-right:10px;margin-bottom:10px}
.about-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin:30px 0}
.about-card{background:var(--light);padding:24px;border-radius:var(--radius);border-left:5px solid var(--yellow)}
.about-card h3{margin:0 0 8px}
.about-card p{margin:0;color:var(--gray);font-size:15px}
.contact-card{background:var(--light);padding:28px;border-radius:var(--radius);border-left:5px solid var(--yellow);margin-top:24px}
.contact-card p{margin:0 0 18px;font-size:16px}
.contact-card a{color:var(--pink);font-weight:700}
.form-card{background:var(--light);padding:26px;border-radius:var(--radius);display:flex;flex-direction:column;gap:16px;text-align:left;margin-top:20px}
.form-card.wide{max-width:720px}
.form-card label{display:flex;flex-direction:column;gap:6px;font-weight:600;font-size:14px}
.form-card input,.form-card textarea,.form-card select{padding:12px 14px;border:1.5px solid var(--border);border-radius:10px;font-size:15px;font-family:inherit;outline:none}
.form-card input:focus,.form-card textarea:focus{border-color:var(--yellow)}
.form-card .two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.admin-table{width:100%;border-collapse:collapse;font-size:14px;margin-top:10px}
.admin-table th,.admin-table td{padding:10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:middle}
.admin-table img{width:60px;height:60px;object-fit:cover;border-radius:8px}
.ellipsis{max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.small{font-size:12px}
.footer{border-top:1px solid var(--border);margin-top:60px;padding:40px;background:var(--light)}
.footer-inner{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr;gap:30px}
.footer-logo{width:44px;height:44px;margin-bottom:10px}
.footer h4{margin:0 0 10px;font-size:14px;text-transform:uppercase;letter-spacing:1px;color:var(--gray)}
.footer a{color:var(--pink);font-weight:600;display:flex;align-items:center;gap:8px}
.ig-pic{width:26px;height:26px;border-radius:50%;object-fit:cover}
.copy{max-width:1200px;margin:30px auto 0;padding-top:20px;border-top:1px solid var(--border);text-align:center;font-size:13px;color:var(--gray)}
.empty{grid-column:1/-1;text-align:center;color:var(--gray);padding:40px}
@media (max-width:820px){
  .hero,.detail{grid-template-columns:1fr;padding:40px 20px}
  .hero h1{font-size:36px}
  .section{padding:40px 20px}
  .nav{padding:12px 18px}
  .nav nav a{margin-left:14px;font-size:14px}
  .footer-inner{grid-template-columns:1fr}
  .form-card .two{grid-template-columns:1fr}
}
</style>
</head>
<body>

<header class="nav">
  <a class="brand" href="{{ url_for('home') }}">
    <img src="{{ url_for('static', filename='logo.png') }}" alt="logo" class="brand-logo">
    <span>{{ APP_NAME }}</span>
  </a>
  <nav>
    <a href="{{ url_for('home') }}">Home</a>
    <a href="{{ url_for('gallery') }}">Gallery</a>
    <a href="{{ url_for('about') }}">About</a>
    <a href="{{ url_for('contact') }}">Contact</a>
    {% if session.get('admin') %}
      <a href="{{ url_for('admin') }}" class="btn-sm">Admin</a>
      <a href="{{ url_for('logout') }}" class="btn-sm ghost">Logout</a>
    {% else %}
      <a href="{{ url_for('login') }}" class="btn-sm ghost">Login</a>
    {% endif %}
  </nav>
</header>

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flashes">
      {% for cat, msg in messages %}
        <div class="flash {{ cat }}">{{ msg }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}

<main>{% block content %}{% endblock %}</main>

<footer class="footer">
  <div class="footer-inner">
    <div>
      <img src="{{ url_for('static', filename='logo.png') }}" alt="logo" class="footer-logo">
      <p><strong>{{ APP_NAME }}</strong><br>Daily AI prompt inspiration.</p>
    </div>
    <div>
      <h4>Follow</h4>
      <a href="{{ IG_URL }}" target="_blank" rel="noopener">
        <img src="{{ url_for('static', filename='profile.jpg') }}" alt="IG" class="ig-pic">
        {{ IG_HANDLE }}
      </a>
    </div>
    <div>
      <h4>Contact</h4>
      <a href="mailto:{{ CONTACT_EMAIL }}">{{ CONTACT_EMAIL }}</a>
    </div>
  </div>
  <div class="copy">© {{ year }} {{ APP_NAME }} · All rights reserved</div>
</footer>

</body>
</html>
"""

HOME_HTML = """
{% extends "base.html" %}
{% block title %}{{ APP_NAME }} — Daily AI Prompts{% endblock %}
{% block content %}
<section class="hero">
  <div class="hero-text">
    <h1>Daily <span class="accent">AI Prompts</span> &amp; Image Inspiration</h1>
    <p>Hand-picked prompts from {{ IG_HANDLE }} — copy, paste, create.</p>
    <div class="cta">
      <a class="btn" href="{{ url_for('gallery') }}">Browse Gallery</a>
      <a class="btn ghost" href="{{ IG_URL }}" target="_blank" rel="noopener">Follow on Instagram</a>
    </div>
    <p class="small">{{ total }} prompts and counting.</p>
  </div>
  <div class="hero-img"><img src="{{ url_for('static', filename='profile.jpg') }}" alt="profile"></div>
</section>
<section class="section">
  <h2 class="section-title">Latest Prompts</h2>
  <div class="grid">
    {% for p in latest %}
      <a class="card" href="{{ url_for('prompt_detail', pid=p['id']) }}">
        <img src="{{ url_for('static', filename='uploads/' ~ p['image']) }}" alt="">
        <div class="card-body">
          <span class="tag">{{ p['category'] or 'General' }}</span>
          <p class="prompt-line">{{ p['prompt'][:90] }}{% if p['prompt']|length > 90 %}…{% endif %}</p>
          <span class="tool">{{ p['tool'] or '' }}</span>
        </div>
      </a>
    {% else %}
      <p class="empty">No prompts yet. Log in and add your first one!</p>
    {% endfor %}
  </div>
  <div class="center"><a class="btn" href="{{ url_for('gallery') }}">See all →</a></div>
</section>
{% endblock %}
"""

GALLERY_HTML = """
{% extends "base.html" %}
{% block title %}Gallery — {{ APP_NAME }}{% endblock %}
{% block content %}
<section class="section">
  <h1 class="page-title">Gallery</h1>
  <form class="search" method="get">
    <input type="text" name="q" value="{{ q }}" placeholder="Search prompts, tools, categories…">
    <select name="cat">
      <option value="">All categories</option>
      {% for c in cats %}
        <option value="{{ c }}" {% if c == current_cat %}selected{% endif %}>{{ c }}</option>
      {% endfor %}
    </select>
    <button class="btn" type="submit">Search</button>
  </form>
  <div class="grid">
    {% for p in prompts %}
      <a class="card" href="{{ url_for('prompt_detail', pid=p['id']) }}">
        <img src="{{ url_for('static', filename='uploads/' ~ p['image']) }}" alt="">
        <div class="card-body">
          <span class="tag">{{ p['category'] or 'General' }}</span>
          <p class="prompt-line">{{ p['prompt'][:90] }}{% if p['prompt']|length > 90 %}…{% endif %}</p>
          <span class="tool">{{ p['tool'] or '' }}</span>
        </div>
      </a>
    {% else %}
      <p class="empty">Nothing found. Try a different search.</p>
    {% endfor %}
  </div>
</section>
{% endblock %}
"""

DETAIL_HTML = """
{% extends "base.html" %}
{% block title %}{{ p['prompt'][:40] }} — {{ APP_NAME }}{% endblock %}
{% block content %}
<section class="detail">
  <div class="detail-img"><img src="{{ url_for('static', filename='uploads/' ~ p['image']) }}" alt=""></div>
  <div class="detail-info">
    <span class="tag">{{ p['category'] or 'General' }}</span>
    <h1>Prompt</h1>
    <pre id="promptText" class="prompt-box">{{ p['prompt'] }}</pre>
    <button class="btn" onclick="copyPrompt()">Copy Prompt</button>
    {% if p['tool'] %}<p class="muted">Tool: <strong>{{ p['tool'] }}</strong></p>{% endif %}
    <p class="muted small">Posted {{ p['created_at'] }}</p>
    <a class="btn ghost" href="{{ IG_URL }}" target="_blank" rel="noopener">See more on {{ IG_HANDLE }}</a>
  </div>
</section>
<script>
function copyPrompt() {
  const t = document.getElementById('promptText').innerText;
  navigator.clipboard.writeText(t).then(() => {
    const b = event.target;
    b.textContent = 'Copied!';
    setTimeout(() => b.textContent = 'Copy Prompt', 1500);
  });
}
</script>
{% endblock %}
"""

ABOUT_HTML = """
{% extends "base.html" %}
{% block title %}About — {{ APP_NAME }}{% endblock %}
{% block content %}
<section class="section narrow">
  <h1 class="page-title">About {{ APP_NAME }}</h1>
  <p class="lead">
    {{ APP_NAME }} is the home of the best AI image prompts from
    <a href="{{ IG_URL }}" target="_blank" rel="noopener">{{ IG_HANDLE }}</a>.
    New prompts added daily — copy them, remix them, make them yours.
  </p>
  <div class="about-grid">
    <div class="about-card"><h3>Daily Drops</h3><p>Fresh prompts added every day, straight from the Instagram feed.</p></div>
    <div class="about-card"><h3>Copy & Create</h3><p>One click to copy a prompt. Use it in Midjourney, DALL·E, Stable Diffusion — your pick.</p></div>
    <div class="about-card"><h3>For Creators</h3><p>Whether you're a designer, hobbyist, or AI artist, you'll find inspiration here.</p></div>
  </div>
  <div class="center"><a class="btn" href="{{ IG_URL }}" target="_blank" rel="noopener">Follow {{ IG_HANDLE }}</a></div>
</section>
{% endblock %}
"""

CONTACT_HTML = """
{% extends "base.html" %}
{% block title %}Contact — {{ APP_NAME }}{% endblock %}
{% block content %}
<section class="section narrow">
  <h1 class="page-title">Get in Touch</h1>
  <p class="lead">Questions, collabs, or just want to say hi? Reach out:</p>
  <div class="contact-card">
    <p><strong>Email</strong><br><a href="mailto:{{ CONTACT_EMAIL }}">{{ CONTACT_EMAIL }}</a></p>
    <p><strong>Instagram</strong><br><a href="{{ IG_URL }}" target="_blank" rel="noopener">{{ IG_HANDLE }}</a></p>
  </div>
</section>
{% endblock %}
"""

LOGIN_HTML = """
{% extends "base.html" %}
{% block title %}Login — {{ APP_NAME }}{% endblock %}
{% block content %}
<section class="section narrow center">
  <h1 class="page-title">Admin Login</h1>
  <form method="post" class="form-card">
    <label>Username<input type="text" name="username" required></label>
    <label>Password<input type="password" name="password" required></label>
    <button class="btn" type="submit">Log in</button>
  </form>
</section>
{% endblock %}
"""

ADMIN_HTML = """
{% extends "base.html" %}
{% block title %}Admin — {{ APP_NAME }}{% endblock %}
{% block content %}
<section class="section">
  <h1 class="page-title">Add a new prompt</h1>
  <form method="post" enctype="multipart/form-data" class="form-card wide">
    <label>Image<input type="file" name="image" accept="image/*" required></label>
    <label>Prompt text<textarea name="prompt" rows="5" required placeholder="A hyper-realistic portrait of…"></textarea></label>
    <div class="two">
      <label>Tool<input type="text" name="tool" placeholder="Midjourney / DALL·E / Stable Diffusion"></label>
      <label>Category<input type="text" name="category" placeholder="Portrait / Landscape / Logo…"></label>
    </div>
    <button class="btn" type="submit">Post prompt</button>
  </form>
  <h2 class="section-title">All prompts ({{ prompts|length }})</h2>
  <table class="admin-table">
    <thead><tr><th>Image</th><th>Prompt</th><th>Tool</th><th>Category</th><th>Date</th><th></th></tr></thead>
    <tbody>
    {% for p in prompts %}
      <tr>
        <td><img src="{{ url_for('static', filename='uploads/' ~ p['image']) }}" alt=""></td>
        <td class="ellipsis">{{ p['prompt'][:80] }}</td>
        <td>{{ p['tool'] }}</td>
        <td>{{ p['category'] }}</td>
        <td class="small">{{ p['created_at'] }}</td>
        <td>
          <form method="post" action="{{ url_for('delete', pid=p['id']) }}" onsubmit="return confirm('Delete this prompt?');">
            <button class="btn-sm danger" type="submit">Delete</button>
          </form>
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</section>
{% endblock %}
"""

# This teaches Flask about all the templates above, without needing separate files
app.jinja_loader = None
from jinja2 import DictLoader
app.jinja_env.loader = DictLoader({
    "base.html": BASE_HTML,
    "home.html": HOME_HTML,
    "gallery.html": GALLERY_HTML,
    "prompt_detail.html": DETAIL_HTML,
    "about.html": ABOUT_HTML,
    "contact.html": CONTACT_HTML,
    "login.html": LOGIN_HTML,
    "admin.html": ADMIN_HTML,
})

# ============================================================
#  ROUTES — the actual pages of the website
# ============================================================
@app.route("/")
def home():
    conn = db()
    latest = conn.execute("SELECT * FROM prompts ORDER BY created_at DESC LIMIT 6").fetchall()
    total = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    conn.close()
    return render_template_string(app.jinja_env.loader.mapping["home.html"], latest=latest, total=total)


@app.route("/gallery")
def gallery():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "").strip()
    conn = db()
    sql = "SELECT * FROM prompts"
    params = []
    where = []
    if q:
        where.append("(prompt LIKE ? OR tool LIKE ? OR category LIKE ?)")
        params += [f"%{q}%"] * 3
    if cat:
        where.append("category = ?")
        params.append(cat)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC"
    prompts = conn.execute(sql, params).fetchall()
    cats = [r[0] for r in conn.execute("SELECT DISTINCT category FROM prompts WHERE category != ''").fetchall()]
    conn.close()
    return render_template_string(app.jinja_env.loader.mapping["gallery.html"],
                                   prompts=prompts, cats=cats, q=q, current_cat=cat)


@app.route("/prompt/<int:pid>")
def prompt_detail(pid):
    conn = db()
    p = conn.execute("SELECT * FROM prompts WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not p:
        abort(404)
    return render_template_string(app.jinja_env.loader.mapping["prompt_detail.html"], p=p)


@app.route("/about")
def about():
    return render_template_string(app.jinja_env.loader.mapping["about.html"])


@app.route("/contact")
def contact():
    return render_template_string(app.jinja_env.loader.mapping["contact.html"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        pw = request.form.get("password", "")
        if u == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session["admin"] = True
            flash("Welcome back!", "success")
            return redirect(url_for("admin"))
        flash("Wrong username or password.", "error")
    return render_template_string(app.jinja_env.loader.mapping["login.html"])


@app.route("/logout")
def logout():
    session.pop("admin", None)
    flash("Logged out.", "success")
    return redirect(url_for("home"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        tool = request.form.get("tool", "").strip()
        category = request.form.get("category", "").strip()
        file = request.files.get("image")

        if not prompt or not file or file.filename == "":
            flash("Prompt text and image are required.", "error")
            return redirect(url_for("admin"))
        if not allowed_file(file.filename):
            flash("Only PNG, JPG, JPEG, WEBP, GIF allowed.", "error")
            return redirect(url_for("admin"))

        fname = secure_filename(file.filename)
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        fname = f"{stamp}_{fname}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        file.save(path)

        try:
            img = Image.open(path)
            if img.width > 1600:
                ratio = 1600 / img.width
                img = img.resize((1600, int(img.height * ratio)))
                img.save(path, optimize=True, quality=85)
        except Exception:
            pass

        conn = db()
        conn.execute(
            "INSERT INTO prompts (image, prompt, tool, category, created_at) VALUES (?, ?, ?, ?, ?)",
            (fname, prompt, tool, category, datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()
        conn.close()
        flash("Prompt posted!", "success")
        return redirect(url_for("admin"))

    conn = db()
    prompts = conn.execute("SELECT * FROM prompts ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template_string(app.jinja_env.loader.mapping["admin.html"], prompts=prompts)


@app.route("/delete/<int:pid>", methods=["POST"])
@login_required
def delete(pid):
    conn = db()
    row = conn.execute("SELECT image FROM prompts WHERE id=?", (pid,)).fetchone()
    if row:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], row["image"]))
        except OSError:
            pass
        conn.execute("DELETE FROM prompts WHERE id=?", (pid,))
        conn.commit()
    conn.close()
    flash("Deleted.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
