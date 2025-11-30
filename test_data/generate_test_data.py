#!/usr/bin/env python3
"""
Generate test CSV files for the Cosmetics Records import feature.

Creates:
- clients.csv: 100 clients with various personal data
- treatments.csv: ~1500 treatment records (5-30 per client)
- product_sales.csv: ~1000 product sales (3-20 per client)
- inventory.csv: 78 inventory items
"""

import csv
import random
from datetime import date, timedelta

# Seed for reproducibility
random.seed(42)

# ============================================================================
# Sample Data
# ============================================================================

FIRST_NAMES_FEMALE = [
    "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia",
    "Harper", "Evelyn", "Abigail", "Emily", "Elizabeth", "Sofia", "Avery",
    "Ella", "Scarlett", "Grace", "Chloe", "Victoria", "Riley", "Aria", "Lily",
    "Aurora", "Zoey", "Nora", "Hannah", "Lillian", "Addison", "Eleanor",
    "Natalie", "Luna", "Savannah", "Brooklyn", "Leah", "Zoe", "Stella",
    "Hazel", "Ellie", "Paisley", "Audrey", "Skylar", "Violet", "Claire",
    "Bella", "Lucy", "Anna", "Caroline", "Genesis", "Aaliyah", "Kennedy",
    "Maria", "Laura", "Sarah", "Jennifer", "Michelle", "Amanda", "Jessica",
    "Stephanie", "Rebecca", "Nicole", "Sandra", "Kathleen", "Pamela",
]

FIRST_NAMES_MALE = [
    "James", "Michael", "Robert", "John", "David", "William", "Richard",
    "Joseph", "Thomas", "Christopher", "Daniel", "Matthew", "Anthony",
    "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Mueller", "Schmidt", "Fischer", "Weber", "Schulz",
    "Wagner", "Becker", "Hoffmann", "Schaefer", "Koch", "Richter", "Klein",
]

STREET_NAMES = [
    "Main Street", "Oak Avenue", "Maple Drive", "Cedar Lane", "Pine Road",
    "Elm Street", "Park Avenue", "Lake Drive", "River Road", "Hill Street",
    "Forest Lane", "Meadow Way", "Spring Street", "Valley Road", "Garden Path",
    "Sunset Boulevard", "Mountain View", "Ocean Drive", "Beach Road", "Harbor Lane",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "Seattle", "Denver", "Boston",
    "Portland", "Miami", "Atlanta", "Minneapolis", "Oakland", "Sacramento",
]

ALLERGIES = [
    "Latex", "Fragrance", "Parabens", "Salicylic acid", "Retinol",
    "Essential oils", "Lanolin", "Formaldehyde", "Nickel", "Cobalt",
    "Propylene glycol", "Sulfates", "Benzoyl peroxide", "AHA/BHA",
    "Vitamin C (high concentration)", "Tea tree oil", "Coconut derivatives",
]

TAGS = [
    "VIP", "Regular", "New client", "Sensitive skin", "Acne-prone",
    "Mature skin", "Oily skin", "Dry skin", "Combination skin",
    "Rosacea", "Eczema", "Monthly package", "Referred by friend",
    "Wedding prep", "Special occasions", "Anti-aging focus",
]

TREATMENT_TYPES = [
    "Deep cleansing facial",
    "Hydrating facial treatment",
    "Anti-aging facial with LED therapy",
    "Microdermabrasion session",
    "Chemical peel - light",
    "Chemical peel - medium",
    "Acne treatment facial",
    "Brightening vitamin C facial",
    "Oxygen facial treatment",
    "Collagen boost facial",
    "Dermaplaning treatment",
    "Microneedling session",
    "Lymphatic drainage massage",
    "Eye contour treatment",
    "Lip treatment",
    "Back facial treatment",
    "Neck and décolletage treatment",
    "Express facial (30 min)",
    "Signature facial (90 min)",
    "Consultation and skin analysis",
]

TREATMENT_NOTES_TEMPLATES = [
    "{treatment}. Client reported satisfaction with results.",
    "{treatment}. Recommended {product} for home care.",
    "{treatment}. Slight redness post-treatment, advised cold compress.",
    "{treatment}. Client has been regular for {months} months. Good progress on {concern}.",
    "{treatment}. First visit - performed patch test. Schedule follow-up in 2 weeks.",
    "{treatment}. Used {product} during treatment. Client noted immediate improvement.",
    "{treatment}. Adjusted protocol due to {sensitivity}. Client tolerated well.",
    "{treatment}. Combined with {addon}. Excellent results visible.",
    "{treatment}. Client preparing for {event}. Recommended series of treatments.",
    "{treatment}. Follow-up from previous session. {concern} significantly improved.",
    "{treatment}. Discussed home care routine. Provided samples of {product}.",
    "{treatment}. Client experienced minor tingling during treatment - normal reaction.",
    "{treatment}. Added extra hydration step due to dry conditions.",
    "{treatment}. Client very happy with results. Booked next appointment.",
    "{treatment}. Noted improvement in skin texture. Continue current protocol.",
]

CONCERNS = [
    "hyperpigmentation", "fine lines", "acne scarring", "enlarged pores",
    "uneven skin tone", "dehydration", "loss of elasticity", "dullness",
    "dark circles", "sun damage", "texture issues", "redness",
]

SENSITIVITIES = [
    "sensitive areas around nose", "mild rosacea", "recent sun exposure",
    "dry patches on cheeks", "active breakout on chin", "sensitivity to acids",
]

EVENTS = [
    "wedding", "anniversary", "graduation ceremony", "photo shoot",
    "vacation", "important meeting", "reunion", "holiday party",
]

ADDONS = [
    "LED light therapy", "high-frequency treatment", "facial massage",
    "mask upgrade", "eye treatment", "lip treatment", "neck treatment",
]

PRODUCT_BRANDS = [
    "SkinCeuticals", "Dermalogica", "Obagi", "iS Clinical", "ZO Skin Health",
    "PCA Skin", "Image Skincare", "Environ", "Jan Marini", "Revision",
    "Medik8", "AlumierMD", "CosMedix", "Eminence", "HydroPeptide",
]

PRODUCT_TYPES = [
    "Cleanser", "Toner", "Serum", "Moisturizer", "Eye Cream",
    "Sunscreen SPF 50", "Retinol Treatment", "Vitamin C Serum",
    "Hyaluronic Acid Serum", "Exfoliating Pads", "Face Mask",
    "Night Cream", "Brightening Serum", "Acne Spot Treatment",
    "Lip Treatment", "Neck Cream", "Hand Cream", "Body Lotion",
]

INVENTORY_ITEMS = [
    # Cleansers
    ("Gentle Foaming Cleanser", "ml", "Daily gentle cleanser for all skin types"),
    ("Deep Pore Cleansing Gel", "ml", "Oil-control cleanser for oily/combination skin"),
    ("Cream Cleanser Sensitive", "ml", "Ultra-gentle cream cleanser for sensitive skin"),
    ("Micellar Water", "ml", "No-rinse makeup remover and cleanser"),
    ("Enzyme Powder Cleanser", "g", "Exfoliating powder cleanser with papaya enzyme"),

    # Toners
    ("Hydrating Toner Mist", "ml", "Alcohol-free hydrating toner spray"),
    ("Clarifying Toner", "ml", "BHA toner for acne-prone skin"),
    ("Antioxidant Toner", "ml", "Green tea and vitamin C toner"),
    ("Rosewater Toner", "ml", "Soothing rosewater facial mist"),

    # Serums
    ("Vitamin C 15% Serum", "ml", "Brightening antioxidant serum"),
    ("Vitamin C 20% Serum", "ml", "Professional strength vitamin C"),
    ("Hyaluronic Acid Serum", "ml", "Multi-weight hyaluronic acid for deep hydration"),
    ("Niacinamide 10% Serum", "ml", "Pore-minimizing and brightening serum"),
    ("Retinol 0.3% Serum", "ml", "Entry-level retinol for beginners"),
    ("Retinol 0.5% Serum", "ml", "Medium-strength retinol treatment"),
    ("Retinol 1.0% Serum", "ml", "Professional strength retinol"),
    ("Peptide Complex Serum", "ml", "Anti-aging peptide blend"),
    ("Bakuchiol Serum", "ml", "Natural retinol alternative"),
    ("Azelaic Acid Serum", "ml", "For rosacea and hyperpigmentation"),
    ("Salicylic Acid 2% Serum", "ml", "BHA serum for acne"),
    ("Glycolic Acid 10% Serum", "ml", "AHA exfoliating serum"),
    ("Lactic Acid 5% Serum", "ml", "Gentle AHA for sensitive skin"),
    ("Tranexamic Acid Serum", "ml", "For stubborn dark spots"),
    ("Arbutin Brightening Serum", "ml", "Natural skin brightener"),

    # Moisturizers
    ("Lightweight Gel Moisturizer", "ml", "Oil-free hydration for oily skin"),
    ("Rich Repair Cream", "ml", "Intensive moisturizer for dry skin"),
    ("Barrier Repair Cream", "ml", "Ceramide-rich barrier support"),
    ("Oil-Free Moisturizer SPF 30", "ml", "Daily moisturizer with sun protection"),
    ("Overnight Recovery Cream", "ml", "Rich night cream with peptides"),
    ("Soothing Moisturizer", "ml", "For sensitive and reactive skin"),
    ("Anti-Aging Day Cream", "ml", "Firming daily moisturizer"),
    ("Hydrating Sleeping Mask", "ml", "Leave-on overnight hydration treatment"),

    # Eye Care
    ("Brightening Eye Cream", "ml", "For dark circles and puffiness"),
    ("Firming Eye Serum", "ml", "Peptide eye treatment"),
    ("Retinol Eye Cream", "ml", "Anti-wrinkle eye treatment"),
    ("Caffeine Eye Gel", "ml", "De-puffing eye treatment"),

    # Sunscreens
    ("Mineral Sunscreen SPF 50", "ml", "Zinc oxide physical sunscreen"),
    ("Chemical Sunscreen SPF 50", "ml", "Lightweight daily protection"),
    ("Tinted Sunscreen SPF 45", "ml", "With iron oxides for visible light protection"),
    ("Sunscreen Spray SPF 50", "ml", "Easy application body sunscreen"),
    ("Lip Sunscreen SPF 30", "g", "Moisturizing lip protection"),

    # Masks
    ("Hydrating Sheet Mask", "Pc.", "Single-use intensive hydration"),
    ("Clay Purifying Mask", "ml", "Deep cleansing for oily skin"),
    ("Enzyme Exfoliating Mask", "ml", "Gentle fruit enzyme mask"),
    ("Vitamin C Brightening Mask", "ml", "Glow-boosting treatment"),
    ("Collagen Boost Mask", "ml", "Firming and plumping mask"),
    ("Soothing Gel Mask", "ml", "Calming mask for sensitive skin"),
    ("Charcoal Detox Mask", "ml", "Pore-clarifying treatment"),
    ("Gold Hydrogel Mask", "Pc.", "Luxury firming treatment"),
    ("Bio-Cellulose Mask", "Pc.", "Second-skin hydration mask"),

    # Exfoliants
    ("Microdermabrasion Crystals", "g", "Professional exfoliation treatment"),
    ("Glycolic Peel 30%", "ml", "Light chemical peel"),
    ("Glycolic Peel 50%", "ml", "Medium chemical peel"),
    ("Salicylic Peel 20%", "ml", "For acne-prone skin"),
    ("Lactic Peel 40%", "ml", "Gentle peel for sensitive skin"),
    ("Enzyme Peel Powder", "g", "Natural fruit enzyme exfoliant"),
    ("Physical Exfoliant Scrub", "ml", "Gentle grain scrub"),

    # Professional Products
    ("Numbing Cream", "g", "Pre-treatment numbing agent"),
    ("Aftercare Healing Balm", "g", "Post-treatment skin recovery"),
    ("Hydrating Ampoule", "ml", "Concentrated treatment booster"),
    ("Vitamin Infusion Ampoule", "ml", "Professional vitamin complex"),
    ("Stem Cell Ampoule", "ml", "Advanced regeneration treatment"),
    ("LED Conductive Gel", "ml", "For use with LED devices"),
    ("Microneedling Serum", "ml", "Hyaluronic serum for needling"),
    ("Oxygen Treatment Solution", "ml", "Oxygen facial product"),

    # Body Products
    ("Body Lotion", "ml", "Daily hydrating body lotion"),
    ("Body Scrub", "g", "Exfoliating body treatment"),
    ("Body Oil", "ml", "Nourishing massage oil"),
    ("Hand Cream", "ml", "Intensive hand moisturizer"),
    ("Foot Cream", "ml", "Hydrating foot treatment"),

    # Tools & Accessories
    ("Facial Sponge Set", "Pc.", "Cleansing sponges (pack of 6)"),
    ("Cotton Pads Premium", "Pc.", "Lint-free cotton rounds (pack of 100)"),
    ("Headband Terry", "Pc.", "Spa headband for treatments"),
    ("Disposable Spatulas", "Pc.", "Hygiene spatulas (pack of 50)"),
    ("Extraction Tool Set", "Pc.", "Professional extraction tools"),
    ("Facial Steamer Solution", "ml", "Purified water with essential oils"),
    ("Sterile Gauze Pads", "Pc.", "Medical-grade gauze for treatments"),
    ("Massage Table Covers", "Pc.", "Disposable hygienic covers"),
]


def generate_phone():
    """Generate a random US phone number."""
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"


def generate_email(first_name, last_name):
    """Generate an email address."""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "hotmail.com"]
    formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}{random.randint(1, 99)}",
    ]
    return f"{random.choice(formats)}@{random.choice(domains)}"


def generate_address():
    """Generate a random address."""
    return f"{random.randint(1, 9999)} {random.choice(STREET_NAMES)}, {random.choice(CITIES)}"


def generate_dob():
    """Generate a date of birth (ages 18-75)."""
    today = date.today()
    age = random.randint(18, 75)
    year = today.year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def generate_treatment_date():
    """Generate a treatment date within the last 2 years."""
    today = date.today()
    days_ago = random.randint(0, 730)
    return today - timedelta(days=days_ago)


def generate_product_date():
    """Generate a product sale date within the last 2 years."""
    today = date.today()
    days_ago = random.randint(0, 730)
    return today - timedelta(days=days_ago)


def generate_treatment_notes():
    """Generate realistic treatment notes."""
    template = random.choice(TREATMENT_NOTES_TEMPLATES)
    treatment = random.choice(TREATMENT_TYPES)
    product = f"{random.choice(PRODUCT_BRANDS)} {random.choice(PRODUCT_TYPES)}"
    concern = random.choice(CONCERNS)
    sensitivity = random.choice(SENSITIVITIES)
    event = random.choice(EVENTS)
    addon = random.choice(ADDONS)
    months = random.randint(3, 24)

    return template.format(
        treatment=treatment,
        product=product,
        concern=concern,
        sensitivity=sensitivity,
        event=event,
        addon=addon,
        months=months,
    )


def generate_product_text():
    """Generate product sale text."""
    num_products = random.randint(1, 4)
    products = []
    for _ in range(num_products):
        qty = random.choice(["1x", "2x", "3x"])
        brand = random.choice(PRODUCT_BRANDS)
        product_type = random.choice(PRODUCT_TYPES)
        products.append(f"{qty} {brand} {product_type}")
    return "\n".join(products)


def generate_clients(count=100):
    """Generate client data."""
    clients = []
    for i in range(1, count + 1):
        # 80% female clients (common for cosmetics)
        if random.random() < 0.8:
            first_name = random.choice(FIRST_NAMES_FEMALE)
        else:
            first_name = random.choice(FIRST_NAMES_MALE)

        last_name = random.choice(LAST_NAMES)

        # Most clients have all fields, some have partial data
        has_full_data = random.random() < 0.85

        client = {
            "import_id": f"C{i:04d}",
            "first_name": first_name,
            "last_name": last_name,
            "email": generate_email(first_name, last_name) if has_full_data or random.random() < 0.7 else "",
            "phone": generate_phone() if has_full_data or random.random() < 0.8 else "",
            "address": generate_address() if has_full_data or random.random() < 0.6 else "",
            "date_of_birth": generate_dob().isoformat() if has_full_data or random.random() < 0.7 else "",
            "allergies": random.choice(ALLERGIES) if random.random() < 0.25 else "",
            "tags": ",".join(random.sample(TAGS, random.randint(0, 3))) if random.random() < 0.7 else "",
            "planned_treatment": random.choice(TREATMENT_TYPES) if random.random() < 0.3 else "",
            "notes": f"Client notes for {first_name}. {random.choice(['Regular visitor.', 'Prefers morning appointments.', 'Referred by existing client.', 'Interested in anti-aging treatments.', ''])}" if random.random() < 0.4 else "",
        }
        clients.append(client)

    return clients


def generate_treatments(clients, min_per_client=5, max_per_client=30):
    """Generate treatment records with multiple treatments per client.

    Each client gets between min_per_client and max_per_client treatments,
    with VIP/Regular clients getting more treatments on average.
    """
    treatments = []

    for client in clients:
        # VIP and Regular clients get more treatments
        tags = client.get("tags", "")
        if "VIP" in tags or "Regular" in tags:
            num_treatments = random.randint(max_per_client // 2, max_per_client)
        elif "New client" in tags:
            num_treatments = random.randint(2, min_per_client + 3)
        else:
            num_treatments = random.randint(min_per_client, max_per_client // 2 + 5)

        # Generate treatments spread over time
        for _ in range(num_treatments):
            treatment = {
                "client_import_id": client["import_id"],
                "treatment_date": generate_treatment_date().isoformat(),
                "treatment_notes": generate_treatment_notes(),
            }
            treatments.append(treatment)

    # Shuffle to mix up the order
    random.shuffle(treatments)
    return treatments


def generate_product_sales(clients, min_per_client=3, max_per_client=20):
    """Generate product sale records with multiple sales per client.

    Each client gets between min_per_client and max_per_client product purchases,
    with VIP/Regular clients buying more products on average.
    """
    products = []

    for client in clients:
        # VIP and Regular clients buy more products
        tags = client.get("tags", "")
        if "VIP" in tags or "Regular" in tags:
            num_products = random.randint(max_per_client // 2, max_per_client)
        elif "New client" in tags:
            num_products = random.randint(1, min_per_client + 2)
        else:
            num_products = random.randint(min_per_client, max_per_client // 2 + 3)

        # Generate product purchases spread over time
        for _ in range(num_products):
            product = {
                "client_import_id": client["import_id"],
                "product_date": generate_product_date().isoformat(),
                "product_text": generate_product_text(),
            }
            products.append(product)

    # Shuffle to mix up the order
    random.shuffle(products)
    return products


def generate_inventory(count=78):
    """Generate inventory items."""
    inventory = []
    # Use predefined items first, then generate more if needed
    items_to_use = INVENTORY_ITEMS[:count]

    for name, unit, description in items_to_use:
        # Generate appropriate capacity based on unit
        if unit == "ml":
            capacity = random.choice([15, 30, 50, 100, 120, 150, 200, 250, 500])
        elif unit == "g":
            capacity = random.choice([15, 30, 50, 75, 100, 150, 200, 250])
        else:  # Pc.
            capacity = random.choice([1, 6, 10, 12, 50, 100])

        inventory.append({
            "name": name,
            "capacity": capacity,
            "unit": unit,
            "description": description,
        })

    return inventory


def write_csv(filename, data, fieldnames):
    """Write data to CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Created {filename} with {len(data)} records")


def main():
    """Generate all test data files."""
    print("Generating test data...")

    # Generate data
    clients = generate_clients(100)
    treatments = generate_treatments(clients)  # ~5-30 per client
    product_sales = generate_product_sales(clients)  # ~3-20 per client
    inventory = generate_inventory(78)

    # Write CSV files
    write_csv(
        "clients.csv",
        clients,
        ["import_id", "first_name", "last_name", "email", "phone", "address",
         "date_of_birth", "allergies", "tags", "planned_treatment", "notes"]
    )

    write_csv(
        "treatments.csv",
        treatments,
        ["client_import_id", "treatment_date", "treatment_notes"]
    )

    write_csv(
        "product_sales.csv",
        product_sales,
        ["client_import_id", "product_date", "product_text"]
    )

    write_csv(
        "inventory.csv",
        inventory,
        ["name", "capacity", "unit", "description"]
    )

    print("\nDone! Test data files created.")


if __name__ == "__main__":
    main()
