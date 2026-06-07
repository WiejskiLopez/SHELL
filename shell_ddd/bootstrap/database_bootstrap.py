from shell_ddd.infrastructure.persistence.sql import create_all_tables, seed_base_data


async def bootstrap_database(url: str) -> None:
    await create_all_tables(url)
    await seed_base_data(url)
