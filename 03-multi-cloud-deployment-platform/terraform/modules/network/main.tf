# -----------------------------------------------------------------------------
# Reusable "network" module.
# Purpose: Provide a single variable interface (cidr, public) that each cloud
# provider implementation honors, so the orchestrator can render the same intent
# for AWS/GCP/Azure.
# Security note: `public` defaults to false (fail-closed). When false, no
# internet gateway / public subnet is created.
# -----------------------------------------------------------------------------

variable "cidr" {
  description = "VPC/VNet CIDR block."
  type        = string
}

variable "public" {
  description = "If true, expose a public subnet + gateway. Defaults closed."
  type        = bool
  default     = false
}

variable "name" {
  description = "Logical network name (used for tagging)."
  type        = string
}

output "cidr" {
  value = var.cidr
}

output "is_public" {
  value = var.public
}

# Provider-specific resources (aws_vpc / google_compute_network /
# azurerm_virtual_network) are implemented in per-provider module variants that
# consume these same variables. Kept abstract here to document the contract.
