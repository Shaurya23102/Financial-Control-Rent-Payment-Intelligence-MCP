<<<<<<< HEAD
# 🏠 Property Management MCP Server

AI-powered Property Management system built as a **Model Context Protocol (MCP)** server. This enables any MCP-compatible AI client (Claude, Cursor, etc.) to manage properties, tenants, rent payments, maintenance, and analytics through natural language.

## ✨ Features

### 🏢 Unit Tracking
- Add buildings and rooms with floor/type details
- Track vacancy status in real-time
- Update room status (vacant, occupied, maintenance, reserved)

### 👤 Tenant Profiles
- Structured digital profiles with contact info
- Government ID verification (Aadhaar, PAN, Passport, etc.)
- Complete tenant history — room assignments, payments, maintenance

### 💰 Rent & Payments
- Record payments with automatic late-fee calculation
- View pending dues with overdue highlights
- Full payment audit trail with filtering

### ⚠️ Late Fees & Escalation
- Configurable grace period + daily late fee per lease
- Auto-calculated penalties on late payments
- 4-tier escalation system (LOW → MEDIUM → HIGH → CRITICAL)
- Recommended actions at each escalation level

### 🔧 Maintenance Management
- Tenants can raise categorized maintenance requests
- Multi-level escalation: Property Manager → Owner → External Contractor
- Track open, escalated, and resolved requests by priority

### 📊 Business Dashboard
- **Occupancy Rate** — overall and per building
- **Revenue Trend** — monthly revenue over past N months
- **Collection Efficiency** — % of expected rent collected

### 📋 Lease Management
- Proactive alerts for expiring leases (next 30 days)
- Linked to tenant assignment and rent calculations

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastMCP** — MCP server framework
- **SQLite** — lightweight embedded database
- **uv** — Python package manager

## 🚀 Setup

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run main.py
```

## 📌 Available Tools (20 total)

| Category | Tools |
|---|---|
| Unit Tracking | `add_building`, `add_room`, `list_vacant_rooms`, `update_room_status` |
| Tenant Profiles | `add_tenant`, `assign_tenant_to_room`, `get_tenant_history`, `record_id_verification` |
| Rent & Payments | `record_payment`, `get_pending_dues`, `get_payment_history` |
| Late Fees & Escalation | `calculate_late_fee`, `get_overdue_escalation_report` |
| Maintenance | `raise_maintenance_request`, `escalate_maintenance_request`, `resolve_maintenance_request`, `get_open_maintenance_requests` |
| Dashboard | `occupancy_rate`, `revenue_trend`, `collection_efficiency` |
| Lease Management | `get_expiring_leases` |
| Utility | `list_all_tools` |

## 🔗 Claude Desktop / Cursor Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "property-manager": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/finance_mcp", "main.py"]
    }
  }
}
```

## 📄 License

MIT
=======
# Financial-Control-Rent-Payment-Intelligence-MCP
things that will truly make never miss or forget payments and automated system-driven reminders. 
1 validation that the payment was made or not 
2 late fees penalty and escalation 
3 list all tools available in mcp 
4 maintanance 
5 sqlite database for adding tenent information Unit tracking: add_building, add_room, list_vacant_rooms, update_room_status
Tenant profiles: add_tenant, assign_tenant_to_room, get_tenant_history, record_id_verification
Rent and payments: record_payment, get_pending_dues, get_payment_history
Dashboard: occupancy_rate, revenue_trend, collection_efficiency
6 
>>>>>>> 94d6452096d38f35a79d12441bb1c05236a99d22
