from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROPERTY_PATH = PROJECT_ROOT / "sample_data" / "legacy_property.csv"
LEASE_PATH = PROJECT_ROOT / "sample_data" / "legacy_lease.csv"
GOLD_VIEW_PATH = PROJECT_ROOT / "sql" / "gold_views" / "vw_property_income_summary.sql"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


class TestLegacyDataQuality(unittest.TestCase):
    def setUp(self) -> None:
        self.properties = read_csv(PROPERTY_PATH)
        self.leases = read_csv(LEASE_PATH)

    def test_property_extract_has_unique_primary_keys(self) -> None:
        property_ids = [row["property_id"] for row in self.properties]

        self.assertTrue(property_ids)
        self.assertEqual(len(property_ids), len(set(property_ids)))

    def test_lease_extract_references_existing_properties(self) -> None:
        property_ids = {row["property_id"] for row in self.properties}
        orphaned_leases = [
            row["lease_id"]
            for row in self.leases
            if row["property_id"] not in property_ids
        ]

        self.assertEqual(orphaned_leases, [])

    def test_financial_amounts_are_positive(self) -> None:
        for row in self.properties:
            self.assertGreater(Decimal(row["market_value"]), Decimal("0"))
            self.assertGreater(int(row["total_units"]), 0)

        for row in self.leases:
            self.assertGreater(Decimal(row["monthly_rent"]), Decimal("0"))
            self.assertGreaterEqual(Decimal(row["security_deposit"]), Decimal("0"))

    def test_active_leases_have_valid_date_ranges(self) -> None:
        for row in self.leases:
            if row["lease_status"] != "Active":
                continue

            lease_start = date.fromisoformat(row["lease_start_date"])
            lease_end = date.fromisoformat(row["lease_end_date"])

            self.assertLess(lease_start, lease_end)

    def test_gold_view_targets_silver_property_income(self) -> None:
        sql_text = GOLD_VIEW_PATH.read_text(encoding="utf-8").lower()

        self.assertIn("create or alter view gold.vw_property_income_summary", sql_text)
        self.assertIn("from silver.property_income", sql_text)
        self.assertIn("occupancy_band", sql_text)


if __name__ == "__main__":
    unittest.main()
