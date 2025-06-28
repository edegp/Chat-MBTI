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
  description = "Application name for the MBTI Diagnosis API"
  type        = string
  default     = "mbti-chat"
}

variable "diagnosis_chat" {
  description = "Enable diagnosis chat service"
  type = object({
    name          = string
    memory_limit  = string
    cpu_limit     = string
    max_instances = number
    min_instances = number
    bucket_name   = string
    db = object({
      tier = string
      name = string
    })
    github = object({
      owner  = string
      repo   = string
      branch = string
    })
    vpc = object({
      subnet_cidr    = string
      connector_name = string
    })
  })
  default = {
    name          = "mbti-diagnosis-chat"
    memory_limit  = "2Gi"
    cpu_limit     = "1000m"
    max_instances = 10
    min_instances = 0
    bucket_name   = "mbti_qa_data_collection"
    db = {
      tier = "db-g1-small"
      name = "mbti_diagnosis"
    }
    github = {
      owner  = "edegp" # Example: edegp
      repo   = "Chat-MBTI"
      branch = "main"
    }
    vpc = {
      subnet_cidr    = "10.8.0.0/24"
      connector_name = "mbti-vpc-conn"
    }
  }
}

# API Keys
variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

variable "ar_hostname" {
  description = "Artifact Registry hostname (e.g. asia-northeast1-docker.pkg.dev)"
  type        = string
}

variable "ar_repository" {
  description = "Artifact Registry repository name"
  type        = string
}

variable "diagnosis_summary" {
  description = "Enable diagnosis summary service"
  type = object({
    name             = string
    memory_limit     = string
    cpu_limit        = string
    max_instances    = number
    min_instances    = number
    fuse_bucket_name = string
    github = object({
      owner  = string
      repo   = string
      branch = string
    })
  })
  default = {
    name             = "mbti-diagnosis-summary"
    memory_limit     = "32Gi"
    cpu_limit        = "4000m"
    max_instances    = 10
    min_instances    = 0
    fuse_bucket_name = "hf-model-cache-chat-mbti-458210"
    github = {
      owner  = "edegp" # Example: edegp
      repo   = "Chat-MBTI"
      branch = "main"
    }
  }
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
