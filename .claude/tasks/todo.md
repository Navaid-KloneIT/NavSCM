# Asset Management Module - Implementation Plan

## Module Overview
Module 14: Asset Management - Manages physical assets used to run the supply chain.

## Sub-Modules (5)
1. **Asset Registry** (AST-00001) - Physical asset database with specs, location, status
2. **Preventive Maintenance** (PM-00001) - Scheduled maintenance tasks with frequency
3. **Breakdown Maintenance** (BM-00001) - Unplanned repairs with downtime tracking
4. **Spare Parts Inventory** (SP-00001) - Parts inventory for maintenance
5. **Asset Depreciation** (DEP-00001) - Financial tracking of asset value over time

## Models Design
- Asset + AssetSpecification (inline)
- PreventiveMaintenance + MaintenanceTask (inline)
- BreakdownMaintenance (links to Asset)
- SparePart + SparePartUsage (inline)
- AssetDepreciation (links to Asset)

## Implementation Checklist
- [ ] App setup (apps/assets/)
- [ ] Models, Forms, Views, URLs, Admin
- [ ] 15 templates (5 list + 5 form + 5 detail)
- [ ] Sidebar navigation
- [ ] Seed command
- [ ] Migrations & verification
- [ ] README update
