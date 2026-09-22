import unittest
from unittest.mock import patch

from mrc_automation_agent.config import MrcConfig
from mrc_automation_agent.email_sender import SmtpEmailSender
from mrc_automation_agent.models import EmailDraft


def make_config() -> MrcConfig:
    return MrcConfig(
        sharepoint_site_url="",
        sharepoint_folder_template="",
        sharepoint_tenant="",
        sharepoint_client_id="",
        sharepoint_thumbprint="",
        sharepoint_certificate_path="",
        sharepoint_certificate_password="",
        smtp_sender_email="sys_DHE_AI_ASSISTANT@intel.com",
        smtp_sender_password="test-password",
        smtp_server="smtpauth.intel.com",
        smtp_port=587,
    )


class SmtpEmailSenderTests(unittest.TestCase):
    @patch("mrc_automation_agent.email_sender.ssl.create_default_context")
    @patch("mrc_automation_agent.email_sender.smtplib.SMTP")
    def test_authenticates_with_starttls_and_sends_html(self, smtp_type, tls_context) -> None:
        client = smtp_type.return_value
        sender = SmtpEmailSender(make_config())
        draft = EmailDraft(
            "Alex",
            "alex@example.com",
            "MRC reminder",
            "<p>Please update.</p>",
            1,
            "key",
        )

        sender.send(draft)
        sender.close()

        smtp_type.assert_called_once_with("smtpauth.intel.com", 587, timeout=30)
        client.starttls.assert_called_once_with(context=tls_context.return_value)
        client.login.assert_called_once_with(
            "sys_DHE_AI_ASSISTANT@intel.com", "test-password"
        )
        message = client.send_message.call_args.args[0]
        self.assertEqual("sys_DHE_AI_ASSISTANT@intel.com", message["From"])
        self.assertEqual("alex@example.com", message["To"])
        self.assertEqual("sys_DHE_AI_ASSISTANT@intel.com", message["Cc"])
        self.assertEqual("MRC reminder", message["Subject"])
        self.assertEqual("html", message.get_content_subtype())
        self.assertIn("<p>Please update.</p>", message.get_content())
        client.quit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()