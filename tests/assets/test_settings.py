import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from modelkit.assets.drivers.gcs import GCSDriverSettings
from modelkit.assets.drivers.local import LocalDriverSettings
from modelkit.assets.drivers.s3 import S3DriverSettings
from modelkit.assets.settings import (
    AssetsManagerSettings,
    DriverSettings,
    RemoteAssetsStoreSettings,
)

test_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "settings_dict, valid, expected_type",
    [
        ({"storage_provider": "notsupported"}, False, None),
        ({"storage_provider": "local"}, False, None),
        ({"storage_provider": "local", "some_other_param": "blabli"}, False, None),
        ({"storage_provider": "local", "bucket": test_path}, True, LocalDriverSettings),
        ({"storage_provider": "gcs", "bucket": test_path}, True, GCSDriverSettings),
        ({"storage_provider": "s3", "bucket": test_path}, True, S3DriverSettings),
        ({"storage_provider": "s3ssm", "bucket": test_path}, True, S3DriverSettings),
    ],
)
def test_driver_settings(settings_dict, valid, expected_type, clean_env):
    if valid:
        driver_settings = DriverSettings(**settings_dict)
        assert isinstance(driver_settings.settings, expected_type)
    else:
        with pytest.raises(ValidationError):
            DriverSettings(**settings_dict)


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("WORKING_DIR", raising=False)
    monkeypatch.delenv("ASSETS_BUCKET_NAME", raising=False)
    monkeypatch.delenv("ASSETS_PREFIX", raising=False)


@pytest.mark.parametrize(
    "settings_dict, valid",
    [
        (
            {
                "remote_store": {
                    "driver": {
                        "storage_provider": "local",
                        "bucket": test_path,
                    },
                    "assetsmanager_prefix": "assets-prefix",
                },
                "assets_dir": test_path,
            },
            True,
        ),
        (
            {
                "remote_store": {"driver": {"storage_provider": "gcs"}},
                "assets_dir": "/some/path",
            },
            False,
        ),
        (
            {
                "remote_store": {
                    "driver": {
                        "storage_provider": "gcs",
                        "bucket": "something-tests",
                    }
                },
                "assets_dir": test_path,
            },
            True,
        ),
        (
            {"remote_store": {"driver": {"storage_provider": "gcs"}}},
            False,
        ),
        (
            {
                "remote_store": {
                    "driver": {"storage_provider": "gcs"},
                    "other_field": "tests",
                }
            },
            False,
        ),
        ({"remote_store": {"driver": {"storage_provider": "local"}}}, False),
    ],
)
def test_assetsmanager_settings(monkeypatch, clean_env, settings_dict, valid):
    if valid:
        assetsmanager_settings = AssetsManagerSettings(**settings_dict)
        assert isinstance(assetsmanager_settings, AssetsManagerSettings)
    else:
        with pytest.raises(ValidationError):
            AssetsManagerSettings(**settings_dict)


@pytest.mark.parametrize(
    "settings_dict, valid",
    [
        (
            {
                "assetsmanager_prefix": "assets-v3",
                "driver": {"storage_provider": "local", "bucket": test_path},
            },
            True,
        ),
        (
            {
                "assetsmanager_prefix": "assets-v3",
                "driver": {
                    "storage_provider": "local",
                    "settings": {"bucket": test_path},
                },
                "timeout_s": 300.0,
            },
            True,
        ),
    ],
)
def test_remote_assets_store_settings(monkeypatch, clean_env, settings_dict, valid):
    if valid:
        assetsmanager_settings = RemoteAssetsStoreSettings(**settings_dict)
        assert isinstance(assetsmanager_settings, RemoteAssetsStoreSettings)
    else:
        with pytest.raises(ValidationError):
            RemoteAssetsStoreSettings(**settings_dict)


def test_assetsmanager_minimal(monkeypatch, clean_env, working_dir):
    monkeypatch.setenv("WORKING_DIR", working_dir)
    monkeypatch.setenv("ASSETS_BUCKET_NAME", "some-bucket")
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")
    settings = AssetsManagerSettings()
    assert settings.remote_store.driver.storage_provider == "gcs"
    assert settings.remote_store.driver.settings == GCSDriverSettings()
    assert settings.remote_store.driver.settings.bucket == "some-bucket"
    assert settings.remote_store.assetsmanager_prefix == "modelkit-assets"
    assert settings.assets_dir == Path(working_dir)


def test_assetsmanager_minimal_provider(monkeypatch, clean_env, working_dir):
    monkeypatch.setenv("WORKING_DIR", working_dir)
    monkeypatch.setenv("STORAGE_PROVIDER", "local")

    settings = AssetsManagerSettings()
    assert not settings.remote_store

    monkeypatch.setenv("ASSETS_BUCKET_NAME", working_dir)
    settings = AssetsManagerSettings()
    assert settings.remote_store.driver.storage_provider == "local"
    assert settings.remote_store.driver.settings == LocalDriverSettings()
    assert settings.remote_store.driver.settings.bucket == Path(working_dir)
    assert settings.assets_dir == Path(working_dir)


def test_assetsmanager_minimal_prefix(monkeypatch, clean_env, working_dir):
    monkeypatch.setenv("WORKING_DIR", working_dir)
    monkeypatch.setenv("ASSETS_BUCKET_NAME", "some-bucket")
    monkeypatch.setenv("ASSETS_PREFIX", "a-prefix")
    monkeypatch.setenv("STORAGE_PROVIDER", "gcs")

    settings = AssetsManagerSettings()
    assert settings.remote_store.driver.storage_provider == "gcs"
    assert settings.remote_store.driver.settings == GCSDriverSettings()
    assert settings.remote_store.driver.settings.bucket == "some-bucket"
    assert settings.remote_store.assetsmanager_prefix == "a-prefix"
    assert settings.assets_dir == Path(working_dir)
