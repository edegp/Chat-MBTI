# Project configuration
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "asia-northeast1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "mbti-diagnosis-api"
}

# Cloud Run configuration
variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "2Gi"
}

# Database configuration
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "mbti_diagnosis"
}

# API Keys
variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

# Billing alerts configuration
variable "enable_billing_alerts" {
  description = "Enable billing budget alerts"
  type        = bool
  default     = false
}

variable "billing_account_id" {
  description = "Billing account ID for budget alerts"
  type        = string
  default     = ""
}

variable "monthly_budget_jpy" {
  description = "Monthly budget in Japanese Yen"
  type        = number
  default     = 5000
}

variable "notification_channels" {
  description = "List of notification channels for billing alerts"
  type        = list(string)
  default     = []
}

variable "github_owner" {
  description = "GitHub repository owner (user or org)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to trigger builds on (regex supported)"
  type        = string
  default     = "main"
}

variable "ar_hostname" {
  description = "Artifact Registry hostname (e.g. asia-northeast1-docker.pkg.dev)"
  type        = string
}

variable "ar_repository" {
  description = "Artifact Registry repository name"
  type        = string
}

variable "gcs_bucket_name" {
  description = "Google Cloud Storage bucket name for data uploads"
  type        = string
}
