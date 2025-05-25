# cython: language_level=3
from flask import Blueprint, jsonify

from src.config import app
from src.models import InstanceMetadata
from src.routes.helper.common_helper import admin_required
from src.utils import get_instance_metadata
from src.logger import get_logger
logger = get_logger(__name__)

experimental_bp = Blueprint("experimental", __name__)

# ec2_metadata.html
@app.route("/api/v1/ec2_metadata", methods=["GET"])
@admin_required
def ec2_metadata():
    instance_data = get_instance_metadata()
    instance_metadata = InstanceMetadata.query.first()
    if not instance_metadata:
        logger.info("Instance metadata not found. Creating new instance metadata.")
        instance_metadata = InstanceMetadata(
            ami_id=instance_data.get("ami-id"),
            ami_launch_index=instance_data.get("ami-launch-index"),
            ami_manifest_path=instance_data.get("ami-manifest-path"),
            block_device_mapping=instance_data.get("block-device-mapping/"),
            events=instance_data.get("events/"),
            hostname=instance_data.get("hostname"),
            identity_credentials=instance_data.get("identity-credentials/"),
            instance_action=instance_data.get("instance-action"),
            instance_id=instance_data.get("instance-id"),
            instance_life_cycle=instance_data.get("instance-life-cycle"),
            instance_type=instance_data.get("instance-type"),
            local_hostname=instance_data.get("local-hostname"),
            local_ipv4=instance_data.get("local-ipv4"),
            mac=instance_data.get("mac"),
            metrics=instance_data.get("metrics/"),
            network=instance_data.get("network/"),
            placement=instance_data.get("placement/"),
            profile=instance_data.get("profile"),
            public_hostname=instance_data.get("public-hostname"),
            public_ipv4=instance_data.get("public-ipv4"),
            public_keys=instance_data.get("public-keys/"),
            region_name=instance_data.get("public-hostname").split(".")[1],
            reservation_id=instance_data.get("reservation-id"),
            security_groups=instance_data.get("security-groups"),
            services=instance_data.get("services/"),
            system=instance_data.get("system"),
        )
        instance_metadata.save()
    else:
        logger.info("Instance metadata found. Updating instance metadata.")
        instance_metadata.ami_id = instance_data.get("ami-id")
        instance_metadata.ami_launch_index = instance_data.get("ami-launch-index")
        instance_metadata.ami_manifest_path = instance_data.get("ami-manifest-path")
        instance_metadata.block_device_mapping = instance_data.get("block-device-mapping/")
        instance_metadata.events = instance_data.get("events/")
        instance_metadata.hostname = instance_data.get("hostname")
        instance_metadata.identity_credentials = instance_data.get("identity-credentials/")
        instance_metadata.instance_action = instance_data.get("instance-action")
        instance_metadata.instance_id = instance_data.get("instance-id")
        instance_metadata.instance_life_cycle = instance_data.get("instance-life-cycle")
        instance_metadata.instance_type = instance_data.get("instance-type")
        instance_metadata.local_hostname = instance_data.get("local-hostname")
        instance_metadata.local_ipv4 = instance_data.get("local-ipv4")
        instance_metadata.mac = instance_data.get("mac")
        instance_metadata.metrics = instance_data.get("metrics/")
        instance_metadata.network = instance_data.get("network/")
        instance_metadata.placement = instance_data.get("placement/")
        instance_metadata.profile = instance_data.get("profile")
        instance_metadata.public_hostname = instance_data.get("public-hostname")
        instance_metadata.public_ipv4 = instance_data.get("public-ipv4")
        instance_metadata.public_keys = instance_data.get("public-keys/")
        instance_metadata.region_name = instance_data.get("public-hostname").split(".")[1]
        instance_metadata.reservation_id = instance_data.get("reservation-id")
        instance_metadata.security_groups = instance_data.get("security-groups")
        instance_metadata.services = instance_data.get("services/")
        instance_metadata.system = instance_data.get("system")
        instance_metadata.save()

    return jsonify(instance_data)