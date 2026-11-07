import re


def classify_reply(message: str) -> str:
    """Classify a recruiter reply using transparent keyword rules."""
    if not message or not message.strip():
        return "Other"

    text = re.sub(r"\s+", " ", message.lower()).strip()

    interview_patterns = [
        r"\binterview\b",
        r"\binterviewing\b",
        r"\btechnical round\b",
        r"\bhr round\b",
        r"\bround \d+\b",
        r"\brecruiter screen\b",
        r"\bphone screen\b",
        r"\bscreening call\b",
        r"\bschedule (?:a|an|the) (?:interview|call)\b",
        r"\b(?:invite|invitation)\s+(?:you\s+)?to\s+(?:an?\s+)?interview\b",
        r"\bwould like to interview you\b",
        r"\binterview availability\b",
        r"\binterview slot\b",
        r"\binterview process\b",
        r"\bmeet with the (?:team|hiring manager)\b",
        r"\bnext step[s]? (?:is|are|will be) an? interview\b",
    ]

    rejection_patterns = [
        r"\bnot moving forward\b",
        r"\bunable to proceed\b",
        r"\bnot selected\b",
        r"\bregret to inform\b",
        r"\bposition has been filled\b",
        r"\bnot shortlisted\b",
        r"\bwill not be proceeding\b",
        r"\bdecided to move forward with other candidates\b",
        r"\bnot a match\b",
    ]

    followup_patterns = [
        r"\bupdated resume\b",
        r"\bexpected ctc\b",
        r"\bcurrent ctc\b",
        r"\bnotice period\b",
        r"\bshare your (?:details|portfolio|linkedin)\b",
        r"\bplease share\b",
        r"\bfill out this form\b",
        r"\bprovide the following details\b",
    ]

    positive_patterns = [
        r"\bprofile looks interesting\b",
        r"\binterested in your profile\b",
        r"\bapplication has been shortlisted\b",
        r"\bshortlisted\b",
        r"\bgood fit for the role\b",
        r"\bwe would like to proceed\b",
        r"\bimpressed with your profile\b",
        r"\bmove to the next stage\b",
    ]

    def matches(patterns):
        return any(re.search(pattern, text) for pattern in patterns)

    # More specific outcomes take priority over generic positive language.
    if matches(interview_patterns):
        return "Interview"
    if matches(rejection_patterns):
        return "Rejected"
    if matches(followup_patterns):
        return "Follow-up"
    if matches(positive_patterns):
        return "Positive"
    return "Other"
