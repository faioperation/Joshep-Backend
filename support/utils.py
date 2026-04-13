from .models import BusinessFAQ
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,From
from django.conf import settings


def get_answer_from_faq(user_query):
    """ডাটাবেজ থেকে উত্তর খুঁজে বের করার লজিক"""
    faqs = BusinessFAQ.objects.all()
    user_query = user_query.lower()

    for faq in faqs:
        # যদি ইউজারের প্রশ্নের ভেতরে ডাটাবেজের কোনো শব্দ থাকে
        if faq.question.lower() in user_query or user_query in faq.question.lower():
            return faq.answer

    # উত্তর না পাওয়া গেলে ডিফল্ট মেসেজ
    return "Thank you for reaching out. Our team will review your message and get back to you shortly."



def generate_ai_reply(user_query):
    """
    ডাটাবেজ থেকে FAQ নিয়ে OpenAI-এর মাধ্যমে স্মার্ট রিপ্লাই জেনারেট করার ফাংশন।
    """
    # ১. ডাটাবেজ থেকে সব FAQ সংগ্রহ করে একটি 'Knowledge Base' তৈরি করা
    all_faqs = BusinessFAQ.objects.all()
    knowledge_context = "Here is our business information for Spartacus Bubble Soccer:\n\n"
    
    for faq in all_faqs:
        knowledge_context += f"Question: {faq.question}\nAnswer: {faq.answer}\n\n"

    # ২. OpenAI ক্লায়েন্ট সেটআপ
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        # ৩. এআই-কে ইনস্ট্রাকশন দেওয়া (Prompt Engineering)
        response = client.chat.completions.create(
            model="gpt-4o", # বা gpt-3.5-turbo ব্যবহার করতে পারেন
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a helpful and professional booking assistant for Spartacus Bubble Soccer. "
                        "Answer customer questions strictly based on the provided Knowledge Base below. "
                        "If you don't know the answer, politely tell them that a human representative will contact them soon. "
                        f"\n\nKnowledge Base:\n{knowledge_context}"
                    )
                },
                {"role": "user", "content": user_query}
            ],
            temperature=0.7 # উত্তরের সৃজনশীলতা নিয়ন্ত্রণের জন্য
        )
        
        # এআই-এর তৈরি করা উত্তরটি রিটার্ন করা
        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Thank you for reaching out! We have received your query and a human team member will get back to you shortly."
    


def send_ai_reply_via_sendgrid(to_email, subject, content):
    """
    আপনার .env থেকে ডাটা নিয়ে প্রফেশনাল ইমেইল পাঠানোর ফাংশন।
    """
    # এখান থেকে .env এর ডাটা লোড হচ্ছে
    from_email = From(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
    
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email Sent! Status: {response.status_code}")
        return True
    except Exception as e:
        print(f" SendGrid Error: {e}")
        return False
    


def send_professional_email(to_email, subject, content):
    """সেন্ডগ্রিড এপিআই ব্যবহার করে মেইল পাঠানোর ফাংশন"""
    message = Mail(
        from_email='your-verified-email@gmail.com', # আপনার ভেরিফাইড মেইল
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"Email Sent! Status Code: {response.status_code}")
        return True
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return False