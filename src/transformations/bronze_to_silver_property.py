"""Transform legacy property and lease extracts into a Silver income dataset.

This script represents the Silver layer of the portfolio project:
raw CSV extracts from a legacy SQL Server estate are standardized, joined,
and aggregated into property-level income metrics for downstream Gold views.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F
except ImportError as exc:  # pragma: no cover - exercised only without PySpark
    raise SystemExit(
        "PySpark is required to run this transformation. "
        "Install it with: pip install pyspark"
    ) from exc


def build_silver_property_income(properties: DataFrame, leases: DataFrame) -> DataFrame:
    """Return one Silver row per property with active lease income metrics."""

    clean_properties = properties.select(
        F.trim("property_id").alias("property_id"),
        F.trim("property_name").alias("property_name"),
        F.trim("property_type").alias("property_type"),
        F.trim("city").alias("city"),
        F.trim("state").alias("state"),
        F.to_date("acquisition_date").alias("acquisition_date"),
        F.col("total_units").cast("int").alias("total_units"),
        F.col("market_value").cast("decimal(18,2)").alias("market_value"),
    )

    clean_leases = leases.select(
        F.trim("lease_id").alias("lease_id"),
        F.trim("property_id").alias("property_id"),
        F.trim("tenant_segment").alias("tenant_segment"),
        F.to_date("lease_start_date").alias("lease_start_date"),
        F.to_date("lease_end_date").alias("lease_end_date"),
        F.col("monthly_rent").cast("decimal(18,2)").alias("monthly_rent"),
        F.col("security_deposit").cast("decimal(18,2)").alias("security_deposit"),
        F.upper(F.trim("lease_status")).alias("lease_status"),
    )

    active_lease_income = (
        clean_leases.where(F.col("lease_status") == "ACTIVE")
        .groupBy("property_id")
        .agg(
            F.count("lease_id").alias("active_lease_count"),
            F.sum("monthly_rent").alias("monthly_rent_roll"),
            F.sum("security_deposit").alias("security_deposit_balance"),
        )
    )

    return (
        clean_properties.join(active_lease_income, on="property_id", how="left")
        .fillna(
            {
                "active_lease_count": 0,
                "monthly_rent_roll": 0,
                "security_deposit_balance": 0,
            }
        )
        .withColumn("annualized_rent", F.col("monthly_rent_roll") * F.lit(12))
        .withColumn(
            "occupancy_rate",
            F.round(F.col("active_lease_count") / F.col("total_units"), 4),
        )
        .withColumn(
            "income_yield",
            F.round(F.col("annualized_rent") / F.col("market_value"), 4),
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Silver property income data.")
    parser.add_argument(
        "--property-path",
        default="sample_data/legacy_property.csv",
        help="Path to the Bronze legacy property CSV extract.",
    )
    parser.add_argument(
        "--lease-path",
        default="sample_data/legacy_lease.csv",
        help="Path to the Bronze legacy lease CSV extract.",
    )
    parser.add_argument(
        "--output-path",
        default="output/silver/property_income",
        help="Directory where the Silver dataset will be written.",
    )
    parser.add_argument(
        "--output-format",
        default="parquet",
        choices=["parquet", "csv"],
        help="Output file format for local portfolio runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    spark = (
        SparkSession.builder.appName("bfsi-reit-bronze-to-silver-property")
        .master("local[*]")
        .getOrCreate()
    )

    properties = spark.read.option("header", True).csv(args.property_path)
    leases = spark.read.option("header", True).csv(args.lease_path)

    silver_property_income = build_silver_property_income(properties, leases)

    output_path = Path(args.output_path).as_posix()
    if args.output_format == "csv":
        silver_property_income.coalesce(1).write.mode("overwrite").option(
            "header", True
        ).csv(output_path)
    else:
        silver_property_income.write.mode("overwrite").parquet(output_path)

    spark.stop()


if __name__ == "__main__":
    main()
