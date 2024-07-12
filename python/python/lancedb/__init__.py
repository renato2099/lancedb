#  Copyright 2023 LanceDB Developers
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import importlib.metadata
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Dict, Optional, Union, Any

__version__ = importlib.metadata.version("lancedb")

from ._lancedb import connect as lancedb_connect
from .common import URI, sanitize_uri
from .db import AsyncConnection, DBConnection, LanceDBConnection
from .remote.db import RemoteDBConnection
from .schema import vector
from .table import AsyncTable


def connect(
    uri: URI,
    *,
    api_key: Optional[str] = None,
    region: str = "us-east-1",
    host_override: Optional[str] = None,
    read_consistency_interval: Optional[timedelta] = None,
    request_thread_pool: Optional[Union[int, ThreadPoolExecutor]] = None,
    **kwargs: Any,
) -> DBConnection:
    """Connect to a LanceDB database.

    Parameters
    ----------
    uri: str or Path
        The uri of the database.
    api_key: str, optional
        If presented, connect to LanceDB cloud.
        Otherwise, connect to a database on file system or cloud storage.
        Can be set via environment variable `LANCEDB_API_KEY`.
    region: str, default "us-east-1"
        The region to use for LanceDB Cloud.
    host_override: str, optional
        The override url for LanceDB Cloud.
    read_consistency_interval: timedelta, default None
        (For LanceDB OSS only)
        The interval at which to check for updates to the table from other
        processes. If None, then consistency is not checked. For performance
        reasons, this is the default. For strong consistency, set this to
        zero seconds. Then every read will check for updates from other
        processes. As a compromise, you can set this to a non-zero timedelta
        for eventual consistency. If more than that interval has passed since
        the last check, then the table will be checked for updates. Note: this
        consistency only applies to read operations. Write operations are
        always consistent.
    request_thread_pool: int or ThreadPoolExecutor, optional
        The thread pool to use for making batch requests to the LanceDB Cloud API.
        If an integer, then a ThreadPoolExecutor will be created with that
        number of threads. If None, then a ThreadPoolExecutor will be created
        with the default number of threads. If a ThreadPoolExecutor, then that
        executor will be used for making requests. This is for LanceDB Cloud
        only and is only used when making batch requests (i.e., passing in
        multiple queries to the search method at once).

    Examples
    --------

    For a local directory, provide a path for the database:

    >>> import lancedb
    >>> db = lancedb.connect("~/.lancedb")

    For object storage, use a URI prefix:

    >>> db = lancedb.connect("s3://my-bucket/lancedb")

    Connect to LanceDB cloud:

    >>> db = lancedb.connect("db://my_database", api_key="ldb_...")

    Returns
    -------
    conn : DBConnection
        A connection to a LanceDB database.
    """
    if isinstance(uri, str) and uri.startswith("db://"):
        if api_key is None:
            api_key = os.environ.get("LANCEDB_API_KEY")
        if api_key is None:
            raise ValueError(f"api_key is required to connected LanceDB cloud: {uri}")
        if isinstance(request_thread_pool, int):
            request_thread_pool = ThreadPoolExecutor(request_thread_pool)
        return RemoteDBConnection(
            uri,
            api_key,
            region,
            host_override,
            request_thread_pool=request_thread_pool,
            **kwargs,
        )

    if kwargs:
        raise ValueError(f"Unknown keyword arguments: {kwargs}")
    return LanceDBConnection(uri, read_consistency_interval=read_consistency_interval)


async def connect_async(
    uri: URI,
    *,
    api_key: Optional[str] = None,
    region: str = "us-east-1",
    host_override: Optional[str] = None,
    read_consistency_interval: Optional[timedelta] = None,
    request_thread_pool: Optional[Union[int, ThreadPoolExecutor]] = None,
    storage_options: Optional[Dict[str, str]] = None,
) -> AsyncConnection:
    """Connect to a LanceDB database.

    Parameters
    ----------
    uri: str or Path
        The uri of the database.
    api_key: str, optional
        If present, connect to LanceDB cloud.
        Otherwise, connect to a database on file system or cloud storage.
        Can be set via environment variable `LANCEDB_API_KEY`.
    region: str, default "us-east-1"
        The region to use for LanceDB Cloud.
    host_override: str, optional
        The override url for LanceDB Cloud.
    read_consistency_interval: timedelta, default None
        (For LanceDB OSS only)
        The interval at which to check for updates to the table from other
        processes. If None, then consistency is not checked. For performance
        reasons, this is the default. For strong consistency, set this to
        zero seconds. Then every read will check for updates from other
        processes. As a compromise, you can set this to a non-zero timedelta
        for eventual consistency. If more than that interval has passed since
        the last check, then the table will be checked for updates. Note: this
        consistency only applies to read operations. Write operations are
        always consistent.
    storage_options: dict, optional
        Additional options for the storage backend. See available options at
        https://lancedb.github.io/lancedb/guides/storage/

    Examples
    --------

    >>> import lancedb
    >>> async def doctest_example():
    ...     # For a local directory, provide a path to the database
    ...     db = await lancedb.connect_async("~/.lancedb")
    ...     # For object storage, use a URI prefix
    ...     db = await lancedb.connect_async("s3://my-bucket/lancedb")

    Returns
    -------
    conn : AsyncConnection
        A connection to a LanceDB database.
    """
    if read_consistency_interval is not None:
        read_consistency_interval_secs = read_consistency_interval.total_seconds()
    else:
        read_consistency_interval_secs = None

    return AsyncConnection(
        await lancedb_connect(
            sanitize_uri(uri),
            api_key,
            region,
            host_override,
            read_consistency_interval_secs,
            storage_options,
        )
    )


__all__ = [
    "connect",
    "connect_async",
    "AsyncConnection",
    "AsyncTable",
    "URI",
    "sanitize_uri",
    "vector",
    "DBConnection",
    "LanceDBConnection",
    "RemoteDBConnection",
    "__version__",
]
