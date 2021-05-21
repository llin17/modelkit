import os

from modelkit.assets.manager import AssetsManager
from modelkit.assets.settings import AssetSpec
from modelkit.core.model_configuration import configure
from modelkit.core.service import download_assets
from modelkit.log import logger
from modelkit.utils.tensorflow import write_config


def deploy_tf_models(
    required_models, mode, config_name="config", verbose=False, models=None
):
    manager = AssetsManager()
    configuration = configure(models=models)
    model_paths = {}
    for model_name in required_models:
        model_configuration = configuration[model_name]
        if not model_configuration.asset:
            raise ValueError("Is this a TensorFlow model with an asset?")
        spec = AssetSpec.from_string(model_configuration.asset)
        if mode == "local-docker":
            model_paths[model_name] = os.path.join(
                "/config",
                f"{spec.name}/{spec.major_version}.{spec.minor_version}",
            )
        elif mode == "local-process":
            model_paths[model_name] = os.path.join(
                manager.assets_dir,
                f"{spec.name}/{spec.major_version}.{spec.minor_version}",
            )
        elif mode == "remote":
            object_name = manager.get_object_name(
                spec.name, f"{spec.major_version}.{spec.minor_version}"
            )
            model_paths[model_name] = f"gs://{manager.bucket}/{object_name}"
        if spec.sub_part:
            model_paths[model_name] += spec.sub_part

    if mode == "local-docker" or mode == "local-process":
        logger.info("Checking that local models are present.")
        download_assets(configuration=configuration, required_models=required_models)
        target = os.path.join(manager.assets_dir, f"{config_name}.config")
    logger.info(
        "Writing TF serving configuration locally.",
        config_name=config_name,
        target=target,
    )
    write_config(target, model_paths, verbose=verbose)
