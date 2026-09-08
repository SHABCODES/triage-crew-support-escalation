import os
import uuid
import datetime
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
os.environ['LANGCHAIN_PROJECT'] = 'triagecrew'

client = Client()
run_id = uuid.uuid4()
now = datetime.datetime.now(datetime.timezone.utc)

client.create_run(
    id=run_id,
    name='TriageCrew System Check',
    run_type='chain',
    start_time=now,
    inputs={'ticket': 'Testing observability wiring'},
    outputs={'status': 'SUCCESS', 'message': 'LangSmith tracing is fully operational!'},
    end_time=now
)
print("Trace pushed!")
