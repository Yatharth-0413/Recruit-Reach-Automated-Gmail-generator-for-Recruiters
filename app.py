import os
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from pathlib import Path
from datetime import datetime, timedelta

from streamlit_autorefresh import st_autorefresh

from database import Application, SessionLocal
from gmail.sender import send_application_email
from gmail.reply_tracker import sync_replies


# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Gmail Parser",
    page_icon="📩",
    layout="wide"
)

os.makedirs("data", exist_ok=True)
os.makedirs("attachments", exist_ok=True)

# ==================================================
# VISUAL THEME — GLOW / GLASS DASHBOARD
# ==================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ink: #f4f6ff;
        --muted: #a8b1ce;
        --panel: rgba(20, 28, 55, 0.72);
        --panel-border: rgba(150, 169, 255, 0.18);
        --violet: #8b5cf6;
        --cyan: #22d3ee;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: #080d1d !important;
        color: var(--ink) !important;
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 12% 8%, rgba(91, 63, 190, .28), transparent 34%),
            radial-gradient(ellipse at 88% 18%, rgba(0, 174, 210, .19), transparent 30%),
            radial-gradient(ellipse at 70% 90%, rgba(117, 54, 190, .18), transparent 34%),
            linear-gradient(135deg, #080d1d 0%, #10172e 48%, #090e20 100%) !important;
        background-attachment: fixed !important;
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: .55;
        background: radial-gradient(circle at 50% 0%, rgba(120, 105, 255, .12), transparent 45%);
        animation: ambientGlow 10s ease-in-out infinite alternate;
    }

    @keyframes ambientGlow {
        from { opacity: .28; transform: scale(1); }
        to { opacity: .7; transform: scale(1.06); }
    }

    /* Keep Streamlit's native header and controls. Make the header
       transparent so it blends into the dashboard background instead
       of appearing as a separate dark strip. */
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {
        background: transparent !important;
        box-shadow: none !important;
        z-index: 1000 !important;
    }

    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 1001 !important;
    }

    [data-testid="stMain"] > div {
        background: transparent !important;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2.8rem;
        padding-bottom: 3rem;
        position: relative;
        z-index: 1;
    }

    h1, h2, h3, h4, p, label, li, [data-testid="stMarkdownContainer"] {
        color: var(--ink) !important;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -.035em;
    }

    h1 {
        background: linear-gradient(100deg, #ffffff 5%, #c7c9ff 48%, #70e7f4 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 18px rgba(128, 111, 255, .2));
    }

    [data-testid="stCaptionContainer"], .stCaption {
        color: var(--muted) !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 22, 46, .97), rgba(9, 15, 33, .97)) !important;
        border-right: 1px solid rgba(142, 160, 255, .18);
        box-shadow: 12px 0 45px rgba(0, 0, 0, .22);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #f5f6ff !important;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(35, 45, 82, .78), rgba(17, 26, 53, .82));
        border: 1px solid var(--panel-border);
        border-radius: 18px;
        padding: 20px 22px;
        box-shadow: 0 12px 34px rgba(0, 0, 0, .2), inset 0 1px rgba(255,255,255,.06);
        transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: rgba(113, 213, 255, .5);
        box-shadow: 0 14px 38px rgba(63, 112, 255, .16), 0 0 22px rgba(34, 211, 238, .09);
    }

    [data-testid="stMetricLabel"] { color: #b9c4e5 !important; }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'Space Grotesk', sans-serif;
        text-shadow: 0 0 18px rgba(120, 160, 255, .22);
    }

    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"],
    [data-testid="stFileUploader"] section {
        background: var(--panel) !important;
        border: 1px solid var(--panel-border) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(14px);
    }

    [data-testid="stExpander"] summary { color: var(--ink) !important; }
    [data-testid="stExpander"] details { border-radius: 16px; }

    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid var(--panel-border);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 12px 30px rgba(0,0,0,.18);
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stMultiSelect"] > div > div {
        background: rgba(13, 21, 44, .88) !important;
        color: #f4f6ff !important;
        border: 1px solid rgba(145, 164, 255, .24) !important;
        border-radius: 11px !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #7c8cff !important;
        box-shadow: 0 0 0 2px rgba(124, 140, 255, .18) !important;
    }

    [data-testid="stButton"] button,
    [data-testid="stDownloadButton"] button {
        color: white !important;
        background: linear-gradient(105deg, #6554e8, #397eea 58%, #12a9c5) !important;
        border: 1px solid rgba(177, 192, 255, .3) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        box-shadow: 0 7px 22px rgba(65, 91, 220, .25);
        transition: transform .2s ease, box-shadow .2s ease, filter .2s ease;
    }

    [data-testid="stButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px);
        filter: brightness(1.12);
        box-shadow: 0 10px 28px rgba(70, 125, 255, .38), 0 0 18px rgba(34, 211, 238, .16);
        border-color: rgba(190, 220, 255, .65) !important;
    }

    [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
        color: #dce4ff !important;
    }

    hr {
        border-color: rgba(160, 174, 255, .17) !important;
        margin-top: 1.6rem !important;
        margin-bottom: 1.6rem !important;
    }

    [data-testid="stAlert"] {
        background: rgba(27, 39, 72, .78) !important;
        border: 1px solid rgba(143, 163, 255, .2) !important;
        border-radius: 13px !important;
        color: #f4f6ff !important;
    }

    [data-testid="stProgressBar"] > div > div > div > div {
        background: linear-gradient(90deg, #8b5cf6, #22d3ee) !important;
    }

    /* Small glowing brand strip above each page */
    .glow-brand-strip {
        display: flex;
        align-items: center;
        gap: 11px;
        margin: 0 0 22px 0;
        padding: 12px 16px;
        width: fit-content;
        border: 1px solid rgba(151, 169, 255, .22);
        border-radius: 999px;
        background: rgba(24, 34, 68, .55);
        box-shadow: 0 0 26px rgba(105, 94, 255, .12);
        color: #cbd6ff;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .14em;
        text-transform: uppercase;
    }

    .glow-brand-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #5cf2e5;
        box-shadow: 0 0 9px #5cf2e5, 0 0 18px rgba(92, 242, 229, .8);
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation: none !important; transition: none !important; }
    }
    </style>
    <div class="glow-brand-strip"><span class="glow-brand-dot"></span> Gmail Parser <span style="opacity:.55">/</span> Job Search Command Center</div>
    """,
    unsafe_allow_html=True
)


DEFAULT_SUBJECT = (
    "Application for {role} – Yatharth Bhardwaj"
)

DEFAULT_BODY = """Hi {recruiter_name},

I hope you are doing well.

I am reaching out regarding Software Engineering
opportunities at {company}.

I am currently working as an SDE1 at Société Générale,
with experience in Java, Spring Boot and backend development.

Please find my resume attached for your consideration.

I would appreciate it if you could consider my profile
for relevant opportunities.

Regards,
Yatharth Bhardwaj
"""


# ==================================================
# DATABASE HELPER
# ==================================================

def get_applications():

    db = SessionLocal()

    try:

        return db.query(Application).order_by(
            Application.sent_at.desc()
        ).all()

    finally:

        db.close()


# ==================================================
# AUTOMATIC GMAIL SYNCHRONIZATION
# ==================================================

st_autorefresh(
    interval=5 * 60 * 1000,
    key="gmail_auto_refresh"
)

if "last_gmail_sync" not in st.session_state:
    st.session_state["last_gmail_sync"] = None


def perform_sync():

    with st.spinner("Synchronizing Gmail replies..."):

        try:

            stats = sync_replies()

            st.session_state["last_gmail_sync"] = (
                datetime.now()
            )

            st.session_state["last_sync_stats"] = stats

            st.session_state.pop(
                "last_sync_error",
                None
            )

            return True

        except Exception as error:

            st.session_state["last_sync_error"] = str(error)

            return False


# Manual sync
if st.sidebar.button(
    "🔄 Sync Gmail Now",
    use_container_width=True
):

    perform_sync()


# Automatic sync every 5 minutes
last_sync = st.session_state["last_gmail_sync"]

if (
    last_sync is None
    or datetime.now() - last_sync >= timedelta(minutes=5)
):

    perform_sync()


# Sync information
last_sync = st.session_state["last_gmail_sync"]

if last_sync:

    st.sidebar.caption(
        "Last synced: " + last_sync.strftime(
            "%d %b %Y, %I:%M:%S %p"
        )
    )

if st.session_state.get("last_sync_error"):

    st.sidebar.warning(
        "Gmail sync failed. Check authentication "
        "or your internet connection."
    )


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

st.sidebar.divider()

st.sidebar.title("📩 Gmail Parser")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Email Campaigns",
        "Replies"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Personal Job Application Manager"
)


# ==================================================
# LOAD APPLICATIONS
# ==================================================

applications = get_applications()

total = len(applications)

replied = sum(
    1 for app in applications
    if app.replied_at is not None
)

interviews = sum(
    1 for app in applications
    if app.status == "Interview"
    or app.reply_category == "Interview"
)

pending = total - replied

response_rate = (
    replied / total * 100
    if total > 0 else 0
)


# ==================================================
# OVERVIEW PAGE
# ==================================================

if page == "Overview":

    st.title("Application Overview")

    st.caption(
        "Your personal job search command center"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Emails Sent",
        total
    )

    c2.metric(
        "Replies Received",
        replied
    )

    c3.metric(
        "Interviews",
        interviews
    )

    c4.metric(
        "Response Rate",
        f"{response_rate:.1f}%"
    )

    st.divider()

    # Recent applications

    st.subheader("Recent Applications")

    if applications:

        data = []

        for app in applications:

            data.append({

                "Company": app.company,

                "Recruiter": app.recruiter_name,

                "Email": app.recruiter_email,

                "Role": app.role,

                "Status": app.status,

                "Sent At (UTC)": app.sent_at,

                "Replied At (UTC)": app.replied_at

            })

        df = pd.DataFrame(data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # Status chart

        st.subheader("Application Status")

        chart_data = (
            df["Status"]
            .value_counts()
            .reset_index()
        )

        chart_data.columns = [
            "Status",
            "Count"
        ]

        fig = px.pie(
            chart_data,
            names="Status",
            values="Count",
            hole=0.5
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "No applications recorded yet."
        )


# ==================================================
# EMAIL CAMPAIGNS PAGE
# ==================================================

elif page == "Email Campaigns":

    st.title("Email Campaign Manager")

    st.caption(
        "Prepare, personalize and send job applications"
    )

    # Recruiter CSV

    st.subheader("1. Upload recruiter database")

    uploaded_csv = st.file_uploader(
        "Upload recruiter CSV",
        type=["csv"]
    )

    if uploaded_csv:

        try:

            df = pd.read_csv(
                uploaded_csv,
                dtype=str
            ).fillna("")

        except Exception as error:

            st.error(f"CSV error: {error}")
            st.stop()

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )

        required_columns = [
            "recruiter_name",
            "email",
            "company",
            "role"
        ]

        missing = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing:

            st.error(
                f"Missing CSV columns: {missing}"
            )

            st.stop()

        df["email"] = (
            df["email"]
            .str.strip()
            .str.lower()
        )

        valid_mask = df["email"].str.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        valid_df = df[valid_mask].copy()

        duplicate_count = valid_df["email"].duplicated().sum()

        valid_df = valid_df.drop_duplicates(
            subset=["email"],
            keep="first"
        )

        st.write(
            f"Total records: {len(df)} | "
            f"Valid unique emails: {len(valid_df)} | "
            f"Invalid: {(~valid_mask).sum()} | "
            f"Duplicate rows: {duplicate_count}"
        )

        st.dataframe(
            valid_df,
            use_container_width=True,
            hide_index=True
        )

        if valid_df.empty:

            st.warning(
                "No valid recruiter emails found."
            )

            st.stop()

        st.divider()

        # Resume upload

        st.subheader("2. Upload resume")

        uploaded_resume = st.file_uploader(
            "Upload resume PDF",
            type=["pdf"],
            key="resume_upload"
        )

        resume_path = None

        if uploaded_resume:

            filename = Path(
                uploaded_resume.name
            ).name

            resume_path = os.path.join(
                "attachments",
                filename
            )

            with open(resume_path, "wb") as file:

                file.write(
                    uploaded_resume.getbuffer()
                )

            st.session_state["resume_path"] = resume_path

        elif st.session_state.get("resume_path"):

            resume_path = st.session_state["resume_path"]

            if not os.path.exists(resume_path):
                resume_path = None

        if resume_path:

            st.success(
                f"Resume ready: {os.path.basename(resume_path)}"
            )

        st.divider()

        # Email configuration

        st.subheader("3. Configure email")

        subject_template = st.text_input(
            "Email Subject",
            value=DEFAULT_SUBJECT
        )

        body_template = st.text_area(
            "Email Body",
            value=DEFAULT_BODY,
            height=300
        )

        st.caption(
            "Placeholders: {recruiter_name}, "
            "{company}, {role}"
        )

        st.divider()

        # Preview

        st.subheader("4. Email preview")

        selected_preview = st.selectbox(
            "Select recruiter",
            valid_df["email"].tolist()
        )

        preview_row = valid_df[
            valid_df["email"] == selected_preview
        ].iloc[0]

        values = {

            "recruiter_name": preview_row["recruiter_name"],

            "company": preview_row["company"],

            "role": preview_row["role"]

        }

        try:

            preview_subject = subject_template.format(
                **values
            )

            preview_body = body_template.format(
                **values
            )

        except (KeyError, ValueError) as error:

            st.error(
                f"Email template error: {error}"
            )

            st.stop()

        st.text_input(
            "Preview Subject",
            value=preview_subject,
            disabled=True
        )

        st.text_area(
            "Preview Body",
            value=preview_body,
            height=220,
            disabled=True
        )

        st.divider()

        # Recipient selection

        st.subheader("5. Select recipients")

        selected_emails = st.multiselect(
            "Choose recruiters",
            options=valid_df["email"].tolist()
        )

        st.write(
            f"Selected: {len(selected_emails)}"
        )

        max_batch = st.number_input(
            "Maximum emails in this batch",
            min_value=1,
            max_value=20,
            value=5
        )

        delay = st.slider(
            "Delay between emails (seconds)",
            min_value=5,
            max_value=30,
            value=10
        )

        recipients = selected_emails[:int(max_batch)]

        if len(selected_emails) > max_batch:

            st.warning(
                f"Only the first {max_batch} selected "
                "recipients will be processed."
            )

        st.divider()

        # Send

        st.subheader("6. Review and send")

        confirm = st.checkbox(
            "I have reviewed the recipients, "
            "email content and attachment. "
            "I approve sending."
        )

        if st.button(
            "🚀 Send Selected Emails",
            type="primary",
            disabled=(
                not confirm
                or not recipients
                or not resume_path
            )
        ):

            progress = st.progress(0)

            sent_count = 0
            skipped_count = 0
            failed_count = 0

            for index, email in enumerate(recipients):

                row = valid_df[
                    valid_df["email"] == email
                ].iloc[0]

                try:

                    result = send_application_email(

                        to_email=email,

                        recruiter_name=row["recruiter_name"],

                        company=row["company"],

                        role=row["role"],

                        resume_path=resume_path,

                        subject_template=subject_template,

                        body_template=body_template

                    )

                    sent_count += 1

                    st.success(
                        f"Sent to {email}"
                    )

                except ValueError as error:

                    skipped_count += 1

                    st.warning(
                        f"Skipped {email}: {error}"
                    )

                except Exception as error:

                    failed_count += 1

                    st.error(
                        f"Failed: {email} | {error}"
                    )

                progress.progress(
                    (index + 1) / len(recipients)
                )

                if index < len(recipients) - 1:

                    time.sleep(delay)

            st.divider()

            st.success(
                f"Batch completed! Sent: {sent_count}, "
                f"Skipped: {skipped_count}, "
                f"Failed: {failed_count}"
            )

            st.info(
                "Visit Overview to see updated applications."
            )


# ==================================================
# REPLIES PAGE
# ==================================================

elif page == "Replies":

    st.title("Recruiter Replies")

    st.caption(
        "Track incoming responses from recruiters"
    )

    replied_apps = [
        app for app in applications
        if app.replied_at is not None
    ]

    total_replies = sum(
        app.reply_count or 0
        for app in replied_apps
    )

    # Reply-category summary
    category_counts = {}
    for application in replied_apps:
        category = application.reply_category or "Other"
        category_counts[category] = category_counts.get(category, 0) + 1

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Applications with replies",
        len(replied_apps)
    )

    c2.metric(
        "Total incoming messages",
        total_replies
    )

    c3.metric(
        "Positive / Interview",
        category_counts.get("Positive", 0) + category_counts.get("Interview", 0)
    )

    if replied_apps:
        st.subheader("Reply categories")
        category_order = ["Positive", "Interview", "Follow-up", "Rejected", "Other"]
        category_df = pd.DataFrame(
            [
                {"Category": category, "Applications": category_counts.get(category, 0)}
                for category in category_order
                if category_counts.get(category, 0) > 0
            ]
        )
        st.dataframe(
            category_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    if replied_apps:

        for app in replied_apps:

            with st.expander(
                f"{app.company} | {app.recruiter_name} "
                f"| {app.status}"
            ):

                st.write(
                    "**Recruiter:**",
                    app.recruiter_name
                )

                st.write(
                    "**Email:**",
                    app.recruiter_email
                )

                st.write(
                    "**Role:**",
                    app.role
                )

                st.write(
                    "**Current status:**",
                    app.status
                )

                st.write(
                    "**Reply category:**",
                    app.reply_category or "Other"
                )

                st.write(
                    "**Sent at (UTC):**",
                    app.sent_at
                )

                st.write(
                    "**First reply (UTC):**",
                    app.replied_at
                )

                st.write(
                    "**Latest reply (UTC):**",
                    app.last_reply_at
                )

                st.write(
                    "**Incoming messages:**",
                    app.reply_count or 0
                )

                if app.sent_at and app.replied_at:

                    response_time = (
                        app.replied_at - app.sent_at
                    )

                    st.metric(
                        "Recruiter response time",
                        str(response_time)
                    )

                st.divider()

                st.write("**First reply content**")

                st.text(
                    app.reply_content
                    or "No readable text found."
                )

                st.write("**Latest reply content**")

                st.text(
                    app.last_reply_content
                    or "No readable text found."
                )

                st.write(
                    "**Latest reply from:**",
                    app.last_reply_from or "Unknown"
                )

    else:

        st.info(
            "No recruiter replies detected yet. "
            "Use Sync Gmail Now to check your inbox."
        )
