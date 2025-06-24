# Billing budget and alerts
resource "google_billing_budget" "budget" {
  count = var.enable_billing_alerts ? 1 : 0

  billing_account = var.billing_account_id
  display_name    = "${var.app_name} Budget Alert"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "JPY"
      units         = tostring(var.monthly_budget_jpy)
    }
  }

  threshold_rules {
    threshold_percent = 0.5 # 50%
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.8 # 80%
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0 # 100%
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = var.notification_channels
    disable_default_iam_recipients   = false
  }
}
