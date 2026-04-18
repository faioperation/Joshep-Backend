from django.db import models

class BusinessFAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question

class AIEmailLog(models.Model):
    user_email = models.EmailField()
    user_question = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply to {self.user_email} at {self.created_at}"