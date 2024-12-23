# from django.test import TestCase
#
# # Create your tests here.
# import os
# from cerebras.cloud.sdk import Cerebras
#
# client = Cerebras(
#     # This is the default and can be omitted
#     api_key="csk-f5kvept5j6d4dv6y3x66tcj648enhm4rdde24923xwmdkvy3",
# )
# def query(what):
#     chat_completion = client.chat.completions.create(
#         messages=[
#             {
#                 "role": "user",
#                 "content": query,
#             }
#     ],
#         model="llama3.1-8b",
#     )
#     return (chat_completion.choices[0].message.content)
from datetime import datetime
from datetime import datetime, timedelta
import pytz

# Set timezone to IST (UTC+5:30)
ist = pytz.timezone('Asia/Kolkata')

# Get current time in IST and subtract 9 hours
now_ist = datetime.now(ist)
print(now_ist)
today_midnight_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
print(today_midnight_ist)