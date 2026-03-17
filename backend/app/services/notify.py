import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(recipients: list[str], subject: str, body: str):
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured, skipping email")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body, "html"))

    try:
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, recipients, msg.as_string())
        server.quit()
        logger.info(f"Email sent to {recipients}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")


def send_feishu(webhook_url: str, title: str, content: str):
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}},
            "elements": [{"tag": "markdown", "content": content}],
        },
    }
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        logger.info(f"Feishu webhook response: {resp.status_code}")
    except Exception as e:
        logger.error(f"Feishu send failed: {e}")


def build_execution_report(execution_name: str, status: str, total: int, passed: int, failed: int, duration_ms: int) -> tuple[str, str, str]:
    """Returns (subject, html_body, markdown_body)."""
    emoji = "✅" if status == "passed" else "❌"
    subject = f"{emoji} [{status.upper()}] {execution_name}"

    html = f"""
    <h2>{emoji} 测试执行报告</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
      <tr><td><b>执行名称</b></td><td>{execution_name}</td></tr>
      <tr><td><b>状态</b></td><td>{status.upper()}</td></tr>
      <tr><td><b>总用例数</b></td><td>{total}</td></tr>
      <tr><td><b>通过</b></td><td style="color:green;">{passed}</td></tr>
      <tr><td><b>失败</b></td><td style="color:red;">{failed}</td></tr>
      <tr><td><b>耗时</b></td><td>{duration_ms}ms</td></tr>
    </table>
    """

    md = (
        f"**{emoji} 测试执行报告**\n"
        f"- 执行名称: {execution_name}\n"
        f"- 状态: **{status.upper()}**\n"
        f"- 总用例: {total} | 通过: {passed} | 失败: {failed}\n"
        f"- 耗时: {duration_ms}ms"
    )

    return subject, html, md


def notify_execution_complete(execution_name: str, status: str, total: int, passed: int, failed: int, duration_ms: int, channels: list[dict]):
    """Send notifications to all active channels."""
    subject, html_body, md_body = build_execution_report(execution_name, status, total, passed, failed, duration_ms)

    for ch in channels:
        try:
            cfg = json.loads(ch["config"])
            if ch["channel_type"] == "email":
                recipients = [r.strip() for r in cfg.get("recipients", "").split(",") if r.strip()]
                if recipients:
                    send_email(recipients, subject, html_body)
            elif ch["channel_type"] == "feishu":
                webhook_url = cfg.get("webhook_url", "")
                if webhook_url:
                    send_feishu(webhook_url, subject, md_body)
        except Exception as e:
            logger.error(f"Notify channel {ch.get('name')} failed: {e}")
