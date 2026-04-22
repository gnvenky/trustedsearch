"""Python API entrypoint scaffold."""

from trusted_search_py.settings import Settings


def main() -> int:
    settings = Settings()
    print(
        f"Trusted Search API scaffold ready on "
        f"http://{settings.host}:{settings.port} using index {settings.index_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
