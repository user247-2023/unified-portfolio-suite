# -----------------------------------------------------------------------------
# Reusable "app" module.
# Purpose: Common variable interface for deploying the application workload on
# any provider. Per-provider implementations (ECS/Cloud Run/Container Apps)
# consume these same variables, so the orchestrator renders one intent everywhere.
# -----------------------------------------------------------------------------
variable "name" {
  description = "Application name (used for resource naming/tagging)."
  type        = string
}

variable "image" {
  description = "Container image reference (immutable tag/digest recommended)."
  type        = string
}

variable "port" {
  description = "Container listening port."
  type        = number
}

variable "replicas" {
  description = "Desired replica count."
  type        = number
}

variable "subnet_id" {
  description = "Subnet to place the workload in (from the network module)."
  type        = string
}
