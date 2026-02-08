from app.db import engine
from app import models

models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)