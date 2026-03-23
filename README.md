# NavSCM - Supply Chain Management System

A multi-tenant SCM application built with Django and Bootstrap 5.

## Tech Stack

- **Backend:** Django 4.2 LTS, Python 3.10+
- **Database:** MySQL (MariaDB via XAMPP)
- **Frontend:** Bootstrap 5.3, jQuery, Remix Icons
- **Multi-tenancy:** Shared database with login-based tenant isolation
- **Config:** python-decouple for environment variables

## Features

### Module 1: Multi-Tenant Administration (Super Admin)

The technical backbone enabling the SaaS/Multi-tenant nature of the application.

- **Tenant Onboarding** - Automated provisioning of new tenant environments and databases
- **Subscription Management** - Management of pricing plans, billing cycles, and feature access per tenant
- **Role-Based Access Control (RBAC)** - Granular permission settings for users within each tenant
- **Theme & Customization** - White-labeling options allowing tenants to apply their branding/logo
- **Audit Logs & Security** - System-wide logs for data access, changes, and security incident monitoring

### Module 2: Procurement Management

Manages the purchasing of goods and services to ensure cost-effectiveness and timely delivery.

- **Purchase Requisition** - Internal requests for goods with approval workflows (draft → pending → approved/rejected), priority levels, and line items with estimated pricing
- **Request for Quotation (RFQ)** - Creation and distribution of RFQs to multiple vendors, quote comparison matrix, and vendor response tracking
- **Purchase Order (PO) Management** - Generation, approval, amendment, and cancellation of purchase orders with line item tracking and partial receipt support
- **Vendor Portal** - Vendor contacts, PO acknowledgement, and shipment status tracking (preparing → shipped → in transit → delivered)
- **Invoice Reconciliation** - Three-way matching of Purchase Order, Goods Receipt Note (GRN), and Vendor Invoice with automated quantity and price matching
- **Vendor Management** - Vendor master data with contact details, payment terms, tax ID, and activity tracking
- **Item Catalog** - Categorized item/service catalog with unit of measure, pricing, and active/inactive status

### Module 2: Supplier Relationship Management (SRM)

Manages the full supplier lifecycle from onboarding and qualification through performance evaluation, contract management, and risk mitigation.

- **Supplier Onboarding** - Structured vendor qualification workflow (draft → in progress → under review → approved/rejected) with qualification questionnaires and due diligence checks (financial verification, legal compliance, quality certification, insurance, reference checks, site inspection)
- **Supplier Scorecards** - Periodic vendor performance evaluation across four dimensions (delivery, quality, price, responsiveness) with auto-calculated overall scores and ratings (excellent → poor)
- **Contract Management** - Full contract lifecycle for master agreements, purchase agreements, service agreements, NDAs, and SLAs with milestone tracking, document management, auto-renewal alerts, and multi-currency support (USD, EUR, GBP, PKR, AED, SAR, INR, CNY)
- **Supplier Catalog Management** - Vendor-specific product catalogs with supplier part numbers, pricing, minimum order quantities, and lead times linked to the procurement item catalog
- **Risk Assessment** - Comprehensive supplier risk evaluation across financial, geopolitical, compliance, and operational dimensions with likelihood/impact scoring, risk factor identification, and mitigation action tracking with assignments and due dates

### Module 3: Inventory Management

Manages stock levels, warehouse operations, and inventory valuation across multiple locations.

- **Warehouse Management** - Multiple warehouse types (main, branch, transit) with zone-based locations (receiving, storage, picking, shipping)
- **Stock Control** - Real-time stock tracking per item/warehouse/batch with on-hand, reserved, and available quantities
- **Warehouse Transfers** - Inter-warehouse stock movement with approval workflow (draft → pending → in transit → received)
- **Stock Adjustments** - Inventory corrections for write-offs, damage, cycle counts, corrections, and returns with approval flow
- **Reorder Automation** - Configurable reorder rules with safety stock, lead times, and auto-generated reorder suggestions
- **Inventory Valuation** - Stock valuation using FIFO, LIFO, or Weighted Average methods with per-item breakdown

### Authentication & User Management
- Login, registration, forgot password
- Role-based access (super admin, tenant admin, manager, employee, viewer)
- User invite system with token-based acceptance
- User profiles with avatar, job title, department, bio

### Multi-Tenancy
- Shared database with `tenant_id` on all models
- Middleware-based tenant resolution from logged-in user
- Auto-filtered querysets ensure data isolation between tenants
- Subscription plans (Free, Starter, Professional, Enterprise)

### Dashboard
- Clean, intuitive and fully responsive design
- Stat cards with tenant-scoped metrics
- Recent users and invites tables
- Quick action shortcuts

### Theme & Layout Options
- Vertical, Horizontal & Detached layouts
- Light & Dark modes
- Fluid & Boxed width
- Fixed & Scrollable positions
- Light & Dark topbars
- Default, Compact, Small Icon & Icon Hovered sidebars
- Light, Dark & Colored sidebars
- LTR & RTL supported
- Preloader option

### Browser Compatibility
- Chrome (Windows, Mac, Linux)
- Firefox (Windows, Mac, Linux)
- Safari (Mac)
- Microsoft Edge
- And other WebKit browsers

## Setup

### Prerequisites
- Python 3.10+
- MySQL (XAMPP recommended)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Navaid-KloneIT/NavSCM.git
   cd NavSCM
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and update the values for your environment:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=navhcm
   DB_USER=root
   DB_PASSWORD=
   DB_HOST=localhost
   DB_PORT=3306
   ```

5. **Create MySQL database**
   ```sql
   CREATE DATABASE navhcm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Seed sample data**
   ```bash
   python manage.py seed_data
   ```

7b. **Seed procurement data**
   ```bash
   python manage.py seed_procurement
   ```

7c. **Seed SRM data**
   ```bash
   python manage.py seed_srm
   ```

7d. **Seed inventory data**
   ```bash
   python manage.py seed_inventory
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Open in browser**
   ```
   http://localhost:8000
   ```

### Default Login Credentials

After running `seed_data`, the following accounts are available:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Superuser |
| admin_\<tenant-slug\> | password123 | Tenant Admin |
| All other users | password123 | Various roles |

## Project Structure

```
NavSCM/
├── .env                   # Environment variables (not in git)
├── .env.example           # Environment template for new setups
├── apps/
│   ├── core/              # Tenant model, middleware, context processors
│   ├── accounts/          # Auth, users, roles, profiles, invites
│   ├── dashboard/         # Dashboard views & stats
│   ├── procurement/       # Procurement management module
│   │   ├── models.py      # Vendor, Item, PR, RFQ, PO, GRN, Invoice, 3-Way Match
│   │   ├── views.py       # All procurement CRUD & workflow views
│   │   ├── forms.py       # Forms & inline formsets for all models
│   │   ├── urls.py        # URL routing (/procurement/*)
│   │   └── admin.py       # Django admin registration
│   ├── srm/               # Supplier relationship management module
│   │   ├── models.py      # Onboarding, Scorecard, Contract, Catalog, Risk Assessment
│   │   ├── views.py       # All SRM CRUD & workflow views
│   │   ├── forms.py       # Forms & inline formsets for all models
│   │   ├── urls.py        # URL routing (/srm/*)
│   │   └── admin.py       # Django admin registration
│   └── inventory/         # Inventory management module
│       ├── models.py      # Warehouse, StockItem, Transfer, Adjustment, Reorder, Valuation
│       ├── views.py       # All inventory CRUD & workflow views
│       ├── forms.py       # Forms & inline formsets for all models
│       ├── urls.py        # URL routing (/inventory/*)
│       └── admin.py       # Django admin registration
├── config/                # Django settings, URLs, WSGI, ASGI
├── static/
│   ├── css/style.css      # Custom theme CSS (blue & white)
│   └── js/app.js          # Theme engine & UI JavaScript
├── templates/
│   ├── base.html          # Master layout
│   ├── partials/          # Sidebar, topbar, footer, preloader, theme settings
│   ├── auth/              # Login, register, forgot password
│   ├── dashboard/         # Dashboard index
│   ├── accounts/          # User list, invite, profile
│   ├── procurement/       # Procurement templates
│   │   ├── vendor_*.html      # Vendor list, form, detail
│   │   ├── item_*.html        # Item catalog list, form
│   │   ├── category_*.html    # Category list, form
│   │   ├── requisition_*.html # Purchase requisition list, form, detail
│   │   ├── rfq_*.html         # RFQ list, form, detail
│   │   ├── po_*.html          # Purchase order list, form, detail
│   │   ├── grn_*.html         # Goods receipt list, form, detail
│   │   ├── invoice_*.html     # Vendor invoice list, form, detail
│   │   └── reconciliation*.html # 3-way match dashboard & form
│   ├── srm/               # SRM templates
│   │   ├── onboarding_*.html  # Supplier onboarding list, form, detail
│   │   ├── question_*.html    # Qualification question list, form
│   │   ├── period_*.html      # Scorecard period list, form
│   │   ├── scorecard_*.html   # Supplier scorecard list, form, detail
│   │   ├── contract_*.html    # Contract list, form, detail
│   │   ├── catalog_*.html     # Supplier catalog list, form, detail
│   │   └── risk_*.html        # Risk assessment list, form, detail
│   └── inventory/         # Inventory templates
│       ├── warehouse_*.html   # Warehouse list, form, detail
│       ├── stock_*.html       # Stock item list, detail
│       ├── transfer_*.html    # Warehouse transfer list, form, detail
│       ├── adjustment_*.html  # Stock adjustment list, form, detail
│       ├── reorder_*.html     # Reorder rules & suggestions list, form
│       └── valuation_*.html   # Inventory valuation list, form, detail
├── media/                 # User uploads
├── manage.py
└── requirements.txt
```

## Environment Variables

All configuration is managed via the `.env` file using `python-decouple`. See `.env.example` for all available variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | - | Django secret key (required) |
| `DEBUG` | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `DB_ENGINE` | `django.db.backends.mysql` | Database engine |
| `DB_NAME` | `navhcm` | Database name |
| `DB_USER` | `root` | Database username |
| `DB_PASSWORD` | *(empty)* | Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `3306` | Database port |

## Roadmap

A high-level overview of planned modules for the NavSCM platform. Each module will follow the same multi-tenant architecture, design patterns, and UI conventions established in the existing codebase.

| # | Module | Description | Status |
|---|--------|-------------|--------|
| 1 | **Warehouse Management (WMS)** | Inbound/outbound operations, bin/location management, cycle counting, yard management | Planned |
| 2 | **Order Management (OMS)** | Order capture, validation, allocation, backorder management, customer notifications | Planned |
| 3 | **Transportation Management (TMS)** | Route planning, freight audit, carrier management, shipment tracking, load optimization | Planned |
| 4 | **Demand Planning & Forecasting** | Sales forecasting, seasonality analysis, demand sensing, collaborative planning, safety stock calculation | Planned |
| 5 | **Manufacturing / Production** | Bill of materials (BOM), production scheduling, work orders, MRP, shop floor control | Planned |
| 6 | **Quality Management (QMS)** | Quality inspection, non-conformance reports, CAPA, audit management, certificates of analysis | Planned |
| 7 | **Returns Management** | RMA workflows, refund processing, disposition management, return portal, warranty claims | Planned |
| 8 | **Supply Chain Analytics** | Inventory dashboards, procurement analytics, logistics KPIs, financial reporting, predictive analytics | Planned |
| 9 | **Contract & Compliance** | Contract repository, compliance tracking, trade documentation, license management, sustainability tracking | Planned |
| 10 | **Asset Management** | Asset registry, preventive/breakdown maintenance, spare parts inventory, asset depreciation | Planned |
| 11 | **Labor Management** | Labor planning, time & attendance, task assignment, performance tracking, payroll integration | Planned |
| 12 | **Cold Chain Management** | Temperature monitoring (IoT), excursion management, cold storage inventory, compliance reporting | Planned |
| 13 | **Customer Portal** | Order tracking, account management, document retrieval, support ticketing, catalog browsing | Planned |
| 14 | **3PL Management** | Client billing, inventory segregation, SLA management, client integration, warehouse rental | Planned |
| 15 | **Finance & Accounting Integration** | Accounts payable/receivable, landed cost calculation, budgeting, tax management | Planned |
| 16 | **Integration & API Gateway** | ERP connectors (SAP, Oracle), e-commerce integration, IoT gateway, EDI, webhooks | Planned |
