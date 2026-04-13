"""
Seed script: creates 2 tenants with sample users, posts, and comments.
All user passwords are: password123
Run inside the backend container: python seed.py
"""
import os
import sys
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Tenant, User, BlogPost, Comment, PostStatus

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


# ── Tenants ──────────────────────────────────────────────────────────────────

tenant1 = Tenant(name="Tech Enthusiasts", slug="tech-enthusiasts")
tenant2 = Tenant(name="Creative Writers",  slug="creative-writers")
db.add_all([tenant1, tenant2])
db.flush()  # get IDs without committing

# ── Users ─────────────────────────────────────────────────────────────────────

pw = hash_pw("password123")

alice   = User(username="alice",   email="alice@techblog.com",    password_hash=pw, tenant_id=tenant1.id)
bob     = User(username="bob",     email="bob@techblog.com",      password_hash=pw, tenant_id=tenant1.id)
charlie = User(username="charlie", email="charlie@writers.com",   password_hash=pw, tenant_id=tenant2.id)
diana   = User(username="diana",   email="diana@writers.com",     password_hash=pw, tenant_id=tenant2.id)

db.add_all([alice, bob, charlie, diana])
db.flush()

# ── Posts ─────────────────────────────────────────────────────────────────────

post1 = BlogPost(
    title="Getting Started with Python",
    summary="A beginner-friendly introduction to Python programming.",
    content="<h2>Why Python?</h2><p>Python is one of the most popular programming languages in the world. Its clean syntax makes it perfect for beginners, while its powerful libraries make it a favourite for data science, web development, and automation.</p><h2>Your First Script</h2><p>Open a terminal and type <code>python --version</code> to check your installation. Then create a file called <code>hello.py</code> and write:</p><pre><code>print('Hello, World!')</code></pre><p>Run it with <code>python hello.py</code> and you're off!</p>",
    author_id=alice.id,
    tenant_id=tenant1.id,
    status=PostStatus.published,
)

post2 = BlogPost(
    title="Docker Best Practices",
    summary="Tips and tricks to write production-ready Dockerfiles.",
    content="<h2>Keep Images Small</h2><p>Use slim or alpine base images wherever possible. Every megabyte matters in production. Multi-stage builds let you compile in a fat image and copy only the artifacts into a lean runtime image.</p><h2>One Process Per Container</h2><p>Docker containers work best when they run a single process. This keeps them easy to scale, monitor, and replace without side effects.</p><h2>Use .dockerignore</h2><p>Add a <code>.dockerignore</code> file to exclude <code>node_modules</code>, <code>.git</code>, and local secrets from your build context. Smaller context = faster builds.</p>",
    author_id=alice.id,
    tenant_id=tenant1.id,
    status=PostStatus.published,
)

post3 = BlogPost(
    title="React Hooks Explained",
    summary="Demystifying useState, useEffect, and custom hooks.",
    content="<h2>What Are Hooks?</h2><p>Introduced in React 16.8, hooks let you use state and other React features in functional components — no classes needed.</p><h2>useState</h2><p><code>const [count, setCount] = useState(0)</code> gives you a reactive variable and a setter. Every call to <code>setCount</code> triggers a re-render.</p><h2>useEffect</h2><p>Think of <code>useEffect</code> as <em>componentDidMount + componentDidUpdate + componentWillUnmount</em> combined. Return a cleanup function to avoid memory leaks.</p><h2>Custom Hooks</h2><p>Extract repeated logic into a function that starts with <code>use</code>. It can call other hooks and return whatever the component needs.</p>",
    author_id=bob.id,
    tenant_id=tenant1.id,
    status=PostStatus.published,
)

post4 = BlogPost(
    title="The Art of the Short Story",
    summary="What separates a forgettable short story from an unforgettable one?",
    content="<h2>Constraint Is a Gift</h2><p>The short story's limited word count forces every sentence to earn its place. There is no room for filler — each paragraph must reveal character, advance plot, or establish atmosphere.</p><h2>Start in the Middle</h2><p>Resist the urge to set the scene for three pages. Drop the reader into a moment of tension or change. Context can follow.</p><h2>The Ending</h2><p>The best short story endings feel both surprising and inevitable — as though they could not have ended any other way, yet the reader never saw them coming.</p>",
    author_id=charlie.id,
    tenant_id=tenant2.id,
    status=PostStatus.published,
)

post5 = BlogPost(
    title="Writing Compelling Characters",
    summary="Characters that readers remember long after the last page.",
    content="<h2>Desire and Obstacle</h2><p>Every memorable character wants something — even if it is only a glass of water. The gap between desire and the obstacles in their way creates narrative tension.</p><h2>Contradiction Makes It Real</h2><p>Real people are contradictory. A brave character who is terrified of commitment, a generous person who is secretly envious — these contradictions breathe life into fiction.</p><h2>Show, Don't Tell</h2><p>Instead of writing 'she was impatient', show her drumming her fingers on the desk and finishing other people's sentences. Let the reader draw the conclusion.</p>",
    author_id=diana.id,
    tenant_id=tenant2.id,
    status=PostStatus.published,
)

db.add_all([post1, post2, post3, post4, post5])
db.flush()

# ── Comments ──────────────────────────────────────────────────────────────────

comments = [
    # On post1 — Getting Started with Python
    Comment(content="Great intro! I showed this to my younger sibling and they got their first script running in under 10 minutes.", author_id=bob.id,   post_id=post1.id, tenant_id=tenant1.id),
    Comment(content="Would love a follow-up post on virtual environments and pip — that's where most beginners get tripped up.",   author_id=alice.id, post_id=post1.id, tenant_id=tenant1.id),

    # On post2 — Docker Best Practices
    Comment(content="The multi-stage build tip saved us nearly 800 MB on our production image. Huge win.",                          author_id=bob.id,   post_id=post2.id, tenant_id=tenant1.id),
    Comment(content="Don't forget to pin your base image tags! Using 'latest' in production has bitten me before.",                author_id=alice.id, post_id=post2.id, tenant_id=tenant1.id),

    # On post3 — React Hooks
    Comment(content="The useEffect cleanup section finally made it click for me. Thanks for writing this up.",                     author_id=alice.id, post_id=post3.id, tenant_id=tenant1.id),
    Comment(content="Custom hooks are so underrated. I've been able to cut hundreds of lines of repeated logic with them.",        author_id=bob.id,   post_id=post3.id, tenant_id=tenant1.id),

    # On post4 — Art of the Short Story
    Comment(content="'Start in the middle' is advice I wish I'd received years ago. My first drafts always open with too much backstory.", author_id=diana.id,   post_id=post4.id, tenant_id=tenant2.id),
    Comment(content="The point about the ending being both surprising and inevitable is the perfect summary of Carver's work.",           author_id=charlie.id, post_id=post4.id, tenant_id=tenant2.id),

    # On post5 — Writing Compelling Characters
    Comment(content="The 'desire and obstacle' framework is so simple but I keep coming back to it every time I'm stuck.",         author_id=charlie.id, post_id=post5.id, tenant_id=tenant2.id),
    Comment(content="Show, don't tell — the oldest rule in the book, but your example with the drumming fingers really lands.",    author_id=diana.id,   post_id=post5.id, tenant_id=tenant2.id),
]

db.add_all(comments)
db.commit()

print("Seed complete.")
print(f"  Tenant 1: '{tenant1.name}'  —  users: alice, bob  —  posts: {post1.title!r}, {post2.title!r}, {post3.title!r}")
print(f"  Tenant 2: '{tenant2.name}'  —  users: charlie, diana  —  posts: {post4.title!r}, {post5.title!r}")
print("  All passwords: password123")
