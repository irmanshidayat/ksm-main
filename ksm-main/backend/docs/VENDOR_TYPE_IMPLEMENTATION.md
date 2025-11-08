# Vendor Type Implementation

## Overview
Implementasi sistem vendor type untuk membedakan vendor internal dan vendor mitra dalam satu sistem terintegrasi.

## Vendor Types

### 1. Vendor Internal (`internal`)
- **Purpose**: Vendor untuk kebutuhan internal PT KSM
- **Business Model**: `supplier`
- **Approval Process**: Standard approval (admin only)
- **Required Documents**: Business License, Tax ID
- **Use Case**: Pembelian barang untuk kebutuhan internal perusahaan

### 2. Vendor Mitra (`partner`)
- **Purpose**: Vendor sebagai supplier untuk PT KSM yang kemudian dijual kembali
- **Business Models**:
  - `supplier`: Vendor yang menyediakan barang untuk dijual kembali
  - `reseller`: Vendor yang menjual barang dari PT KSM
  - `both`: Vendor yang bisa sebagai supplier dan reseller
- **Approval Process**: Extended approval (admin, legal, finance)
- **Required Documents**: Business License, Tax ID, Bank Account, Reseller Agreement (untuk reseller/both)
- **Use Case**: Partnership untuk bisnis reseller

## Database Schema

### New Fields in `vendors` table:
```sql
vendor_type ENUM('internal', 'partner') DEFAULT 'internal'
business_model ENUM('supplier', 'reseller', 'both') DEFAULT 'supplier'
```

### Indexes:
```sql
INDEX idx_vendor_type (vendor_type)
INDEX idx_vendor_business_model (business_model)
```

## API Endpoints

### Vendor Management
- `GET /api/vendor-approval/requirements/<vendor_id>` - Get approval requirements
- `POST /api/vendor-approval/workflow/<vendor_id>` - Create approval workflow
- `POST /api/vendor-approval/approve/<vendor_id>` - Approve vendor
- `GET /api/vendor-approval/pending` - Get pending approvals
- `GET /api/vendor-approval/requirements-info` - Get requirements info

### Filter & Search
- `GET /api/vendor-catalog/all?vendor_type=internal` - Filter by vendor type
- `GET /api/vendor-catalog/all?business_model=reseller` - Filter by business model

## Frontend Components

### New Components
- `VendorTypeBadge` - Display vendor type and business model badges
- Enhanced `VendorCatalogFilter` - Filter by vendor type and business model
- Enhanced `UploadPenawaranSelector` - Select vendor type during registration

### UI Features
- Color-coded badges for vendor types
- Separate approval workflows for different vendor types
- Enhanced filtering and search capabilities
- Responsive design for desktop, tablet, and mobile

## Approval Workflow

### Vendor Internal
1. **Required Documents**: Business License, Tax ID
2. **Approval Levels**: Admin
3. **Process**: Standard approval process

### Vendor Mitra
1. **Required Documents**: 
   - Supplier: Business License, Tax ID, Bank Account
   - Reseller: Business License, Tax ID, Bank Account, Reseller Agreement
   - Both: Business License, Tax ID, Bank Account, Reseller Agreement
2. **Approval Levels**: Admin, Legal, Finance
3. **Process**: Extended approval with legal and financial review

## Business Logic

### Vendor Registration
- Default vendor type: `internal`
- Default business model: `supplier`
- Validation based on vendor type and business model

### Approval Requirements
- Dynamic requirements based on vendor type and business model
- Extended approval process for partner vendors
- Legal and financial review for partner vendors

### Filtering & Search
- Filter by vendor type (internal/partner)
- Filter by business model (supplier/reseller/both)
- Enhanced search capabilities
- Separate dashboards for different vendor types

## Migration

### Database Migration
```sql
-- Run migration script
source migrations/add_vendor_type_fields.sql
```

### Data Migration
- Existing vendors will be set to `internal` with `supplier` business model
- No data loss during migration
- Backward compatible with existing system

## Benefits

1. **Unified System**: Single system for all vendor types
2. **Flexible Business Models**: Support for different business relationships
3. **Enhanced Approval**: Different approval processes for different vendor types
4. **Better Organization**: Clear separation of vendor types
5. **Scalable**: Easy to add new vendor types or business models
6. **User Friendly**: Intuitive UI with clear visual indicators

## Future Enhancements

1. **Commission Tracking**: For reseller vendors
2. **Performance Metrics**: Separate metrics for different vendor types
3. **Advanced Reporting**: Detailed reports by vendor type and business model
4. **Integration**: API integration with external systems
5. **Automation**: Automated approval workflows based on vendor type
