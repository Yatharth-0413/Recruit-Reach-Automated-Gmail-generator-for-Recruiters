
from gmail.reply_classifier import classify_reply

test_messages = [
    "We would like to schedule an interview with you.",
    "Unfortunately, we will not be moving forward with your application.",
    "Please share your updated resume and notice period.",
    "Your profile looks interesting. We would like to proceed.",
    "Thank you for your email. We will get back to you."
    "We are not having any openings at the moment, but we will keep your profile for future reference.",
    "We are impressed with your profile and would like to move to the next stage.",
    "We regret to inform you that you have not been shortlisted for the position.",
    "Please fill out this form with your details.",
]

for message in test_messages:
    result = classify_reply(message)
    print(f"Message: {message}")
    print(f"Classification: {result}")
    print("-" * 60)
