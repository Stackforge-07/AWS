import os, tempfile
os.environ['DATABASE_URL']='sqlite:///'+tempfile.mkdtemp(prefix='skyguard-test-')+'/test.db'
os.environ['SKYGUARD_MODE']='live'
import pytest
from backend.app.db import Base, engine, initialize, Session

@pytest.fixture
def db():
    Base.metadata.drop_all(engine)
    initialize()
    with Session.begin() as s: yield s
