#!/usr/bin/env python3

import os
import sys
import asyncio
import asyncpg


def check_required_vars():
    """Check if all required environment variables are set."""
    required_vars = ["DATABASE_URL", "OPENAI_API_KEY", "DEBUG"]

    missing_vars = [var for var in required_vars if var not in os.environ]

    if missing_vars:
        print(f"Error: Missing required environment variables: {missing_vars}")
        sys.exit(1)

    print("✓ All required environment variables are set")


async def check_database():
    """Verify database connection."""
    try:
        conn = await asyncpg.connect(os.environ["DATABASE_URL"])
        await conn.close()
        print("✓ Successfully connected to database")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


async def main():
    """Run all environment validation checks."""
    print("\nValidating environment setup...\n")

    # Check environment variables
    check_required_vars()

    # Check database connection
    await check_database()

    print("\nEnvironment validation completed successfully! ✨\n")


if __name__ == "__main__":
    asyncio.run(main())
