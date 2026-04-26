from .models import BusinessFAQ
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,From
from django.conf import settings


def get_answer_from_ai_team_api(question_text):

    url=settings.AI_TEAM_API_URL

    payload ={
        "question":question_text
    }


    try:
        response= request.post(url,json=payload,timeout=30)

        if response.status_code == 200:

            ai_data=response.json()
            return ai_data.get('answer')
        
        else:
            return "AI Team's system is currently down "

    except Exception as e:
        return f"Could not connect to AI Team: {str(e)}"


def get_answer_from_faq(user_query):

    faqs = BusinessFAQ.objects.all()
    user_query = user_query.lower()

    for faq in faqs:

        if faq.question.lower() in user_query or user_query in faq.question.lower():
            return faq.answer


    return "Thank you for reaching out. Our team will review your message and get back to you shortly."


def generate_ai_reply(user_query):

    all_faqs = BusinessFAQ.objects.all()
    knowledge_context = "Here is our business information for Spartacus Bubble Soccer:\n\n"
    
    for faq in all_faqs:
        knowledge_context += f"Question: {faq.question}\nAnswer: {faq.answer}\n\n"

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  
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
            temperature=0.7  
        )
        
         
        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Thank you for reaching out! We have received your query and a human team member will get back to you shortly."
    


def send_ai_reply_via_sendgrid(to_email, subject, content):

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

    message = Mail(
        from_email='your-verified-email@gmail.com', 
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