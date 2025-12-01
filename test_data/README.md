# CSV Import Data Format

This document describes the CSV file formats for importing data into Cosmetics Records. Use these formats to migrate data from other programs or to bulk-import client information.

## Overview

The import system supports four CSV files:

| File | Required | Description |
|------|----------|-------------|
| `clients.csv` | **Yes** | Client contact information and details |
| `treatments.csv` | No | Treatment/service history |
| `product_sales.csv` | No | Product purchase history |
| `inventory.csv` | No | Product inventory items |

## General CSV Guidelines

- **Encoding**: UTF-8 (with or without BOM)
- **Delimiter**: Comma (`,`)
- **Quote character**: Double quotes (`"`) for fields containing commas or newlines
- **Date format**: `YYYY-MM-DD` (e.g., `2024-03-15`)
- **Empty values**: Leave the field empty (no quotes needed)
- **Multiple values**: Use commas within quoted strings for lists (e.g., `"tag1,tag2,tag3"`)

## File Formats

### clients.csv (Required)

Contains client contact information and profile details.

#### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `import_id` | Unique identifier for linking to other files | `C0001` |
| `first_name` | Client's first name | `Maria` |
| `last_name` | Client's last name | `Schmidt` |

#### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| `email` | Email address | `maria.schmidt@email.com` |
| `phone` | Phone number (any format) | `(555) 123-4567` |
| `address` | Full address | `123 Main St, Berlin` |
| `date_of_birth` | Birth date (YYYY-MM-DD) | `1985-06-20` |
| `allergies` | Known allergies (free text) | `Latex, Fragrance` |
| `tags` | Comma-separated tags | `VIP,Sensitive skin,Regular` |
| `planned_treatment` | Planned/recommended treatment | `Hydrating facial` |
| `notes` | General notes about the client | `Prefers morning appointments` |

#### Example

```csv
import_id,first_name,last_name,email,phone,address,date_of_birth,allergies,tags,planned_treatment,notes
C0001,Maria,Schmidt,maria.schmidt@email.com,(555) 123-4567,"123 Main St, Berlin",1985-06-20,Latex,"VIP,Regular",Hydrating facial,Prefers morning appointments
C0002,Anna,Mueller,anna.m@email.com,(555) 987-6543,,1990-03-15,,"Sensitive skin",Anti-aging facial,
C0003,Lisa,Weber,,,,,,,Express facial,New client
```

---

### treatments.csv (Optional)

Contains treatment/service history linked to clients.

#### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `client_import_id` | Links to `import_id` in clients.csv | `C0001` |
| `treatment_date` | Date of treatment (YYYY-MM-DD) | `2024-03-15` |
| `treatment_notes` | Description of the treatment | `Hydrating facial with LED therapy` |

#### Example

```csv
client_import_id,treatment_date,treatment_notes
C0001,2024-03-15,Hydrating facial with LED therapy. Client very satisfied.
C0001,2024-02-10,Express facial. Recommended vitamin C serum for home use.
C0002,2024-03-20,"Chemical peel - light. Slight redness, advised cold compress."
```

**Note**: Treatment notes can contain commas and newlines if enclosed in double quotes.

---

### product_sales.csv (Optional)

Contains product purchase history linked to clients.

#### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `client_import_id` | Links to `import_id` in clients.csv | `C0001` |
| `product_date` | Date of purchase (YYYY-MM-DD) | `2024-03-15` |
| `product_text` | Description of products sold | `2x Vitamin C Serum, 1x Moisturizer` |

#### Example

```csv
client_import_id,product_date,product_text
C0001,2024-03-15,"2x Vitamin C Serum
1x Hydrating Moisturizer
1x SPF 50 Sunscreen"
C0002,2024-03-20,1x Gentle Cleanser
```

**Note**: Product text can span multiple lines if enclosed in double quotes. This is useful for listing multiple items.

---

### inventory.csv (Optional)

Contains product inventory items available in your salon.

#### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `name` | Product name | `Vitamin C Serum` |
| `capacity` | Size/amount (number > 0) | `30` |
| `unit` | Unit of measurement | `ml` |

#### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| `description` | Product description | `Brightening antioxidant serum` |

#### Valid Units

Only these three units are accepted:
- `ml` - milliliters (for liquids, serums, etc.)
- `g` - grams (for creams, powders, etc.)
- `Pc.` - pieces (for items sold individually)

#### Example

```csv
name,capacity,unit,description
Vitamin C 15% Serum,30,ml,Brightening antioxidant serum
Rich Repair Cream,50,g,Intensive moisturizer for dry skin
Hydrating Sheet Mask,12,Pc.,Single-use intensive hydration masks
Gentle Cleanser,200,ml,
```

---

## Migrating from Other Programs

### Step-by-Step Guide

1. **Export your data** from your current program (usually as CSV or Excel)

2. **Create the import_id column** for clients:
   - Add a unique identifier for each client (e.g., `C0001`, `C0002`, ...)
   - This ID links clients to their treatments and purchases

3. **Map your columns** to the format above:
   - Rename columns to match the expected names
   - Combine or split fields as needed (e.g., full name → first_name + last_name)

4. **Format dates** as `YYYY-MM-DD`:
   - Convert `15.03.2024` or `03/15/2024` → `2024-03-15`
   - Most spreadsheet programs can do this with a format function

5. **Clean up special characters**:
   - Ensure the file is saved as UTF-8
   - Wrap fields containing commas in double quotes

6. **Link treatment/product history**:
   - Add the `client_import_id` column matching the client's `import_id`

### Common Transformations

#### Splitting Full Names
If your data has full names in one column:

| Original | → | first_name | last_name |
|----------|---|------------|-----------|
| Maria Schmidt | → | Maria | Schmidt |
| Anna Maria Mueller | → | Anna Maria | Mueller |

In Excel/Sheets: Use `Text to Columns` or formulas like:
- First name: `=LEFT(A1, FIND(" ", A1)-1)`
- Last name: `=RIGHT(A1, LEN(A1)-FIND(" ", A1))`

#### Converting Date Formats
| Original | → | Converted |
|----------|---|-----------|
| 15.03.2024 | → | 2024-03-15 |
| 03/15/2024 | → | 2024-03-15 |
| March 15, 2024 | → | 2024-03-15 |

In Excel: Format cells as `YYYY-MM-DD` or use `=TEXT(A1, "YYYY-MM-DD")`

#### Combining Tags
If tags are in separate columns:

| Tag1 | Tag2 | Tag3 | → | tags |
|------|------|------|---|------|
| VIP | Regular | | → | VIP,Regular |

In Excel: `=TEXTJOIN(",", TRUE, B1, C1, D1)`

---

## Validation

When you import files in Cosmetics Records:

1. Click **Settings** → **Import Data**
2. Select your CSV files
3. Click **Validate** to check for errors
4. Review any validation errors and fix your CSV files
5. Click **Import** to complete the import

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "first_name cannot be empty" | Missing required field | Add the client's first name |
| "Invalid date format" | Date not in YYYY-MM-DD | Convert to YYYY-MM-DD format |
| "Invalid unit" | Unit not ml/g/Pc. | Use only ml, g, or Pc. |
| "client_import_id not found" | Treatment/product references non-existent client | Ensure the import_id exists in clients.csv |

---

## Sample Files

This directory contains sample files you can use as templates:

- `clients.csv` - 100 sample clients
- `treatments.csv` - Sample treatment records
- `product_sales.csv` - Sample product sales
- `inventory.csv` - Sample inventory items

You can use these as a reference or modify them for testing.
