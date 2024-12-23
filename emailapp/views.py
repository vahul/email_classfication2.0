import os
import base64
import pytz
from datetime import datetime
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_groq import ChatGroq
from bs4 import BeautifulSoup
from .models import Email  # Ensure the Email model is imported
import time

# Define SCOPES for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Initialize ChatGroq
llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    temperature=0,
    groq_api_key='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'
)


def count_tokens(text):
    return len(text.split())


def classify_email(email, retries=3):
    query = f"What class does this email belong to in the classes Finance, Social, News, Health, Promotions, Job Offers? Just give me the name. Email: {email}"
    response = llm.invoke(query)
    time.sleep(1)
    return response.content


def summarize(text):
    query = f"Give me the overall summary and mention the key points of the mail {text}. If the mail is empty, say that the mail is empty."
    response = llm.invoke(query)
    return response.content


def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def get_todays_emails(service, start_date=None, end_date=None):
    ist = pytz.timezone('Asia/Kolkata')
    today_midnight = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
    start_timestamp = int(today_midnight.timestamp()) if not start_date else int(start_date.timestamp())
    end_timestamp = int(today_midnight.timestamp()) if not end_date else int(end_date.timestamp())

    query = f"after:{start_timestamp} before:{end_timestamp}"

    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        emails = []

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            email_data = {'sender': 'Unknown', 'subject': 'No Subject', 'body': 'No Content'}
            for header in headers:
                if header['name'] == 'From':
                    email_data['sender'] = header['value']
                elif header['name'] == 'Subject':
                    email_data['subject'] = header['value']
            parts = msg.get('payload', {}).get('parts', [])
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        email_data['body'] = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        email_data['body'] = BeautifulSoup(decoded_body, 'html.parser').get_text()
                        break
            email_data['body'] = summarize(email_data['body'])
            email_text = email_data['subject'] + " " + email_data['body']
            email_data['classification'] = classify_email(email_text)
            emails.append(email_data)

        return emails
    except Exception as error:
        print(f"Error fetching emails: {error}")
        return []


def login_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'emailapp/login.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'emailapp/signup.html', {'form': form})


def home_view(request):
    return render(request, 'emailapp/index.html')


def classify_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    start_date = datetime.fromisoformat(start_date) if start_date else None
    end_date = datetime.fromisoformat(end_date) if end_date else None

    service = get_gmail_service()
    emails = get_todays_emails(service, start_date, end_date)

    # Paginator
    paginator = Paginator(emails, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Save emails to the database
    for email in page_obj.object_list:
        Email.objects.create(
            sender=email['sender'],
            subject=email['subject'],
            body=email['body'],
            classification=email['classification']
        )

    return render(request, 'emailapp/allmails.html', {'emails': page_obj})


def categorized_emails_view(request, category):
    emails = Email.objects.filter(classification__icontains=category)
    paginator = Paginator(emails, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, f'emailapp/{category}_emails.html', {'emails': page_obj})


def finance_emails(request):
    return categorized_emails_view(request, 'Finance')


def social_emails(request):
    return categorized_emails_view(request, 'Social')


def news_emails(request):
    return categorized_emails_view(request, 'News')


def health_emails(request):
    return categorized_emails_view(request, 'Health')


def promotions_emails(request):
    return categorized_emails_view(request, 'Promotions')


def job_emails(request):
    return categorized_emails_view(request, 'Job Offers')
