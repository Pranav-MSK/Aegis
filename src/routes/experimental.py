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
            ami_id=instance_data.get("ami-id"), # type: ignore
            ami_launch_index=instance_data.get("ami-launch-index"), # type: ignore
            ami_manifest_path=instance_data.get("ami-manifest-path"), # type: ignore
            block_device_mapping=instance_data.get("block-device-mapping/"), # type: ignore
            events=instance_data.get("events/"), # type: ignore
            hostname=instance_data.get("hostname"), # type: ignore
            identity_credentials=instance_data.get("identity-credentials/"), # type: ignore
            instance_action=instance_data.get("instance-action"), # type: ignore
            instance_id=instance_data.get("instance-id"), # type: ignore
            instance_life_cycle=instance_data.get("instance-life-cycle"), # type: ignore
            instance_type=instance_data.get("instance-type"), # type: ignore
            local_hostname=instance_data.get("local-hostname"), # type: ignore
            local_ipv4=instance_data.get("local-ipv4"), # type: ignore
            mac=instance_data.get("mac"), # type: ignore
            metrics=instance_data.get("metrics/"), # type: ignore
            network=instance_data.get("network/"), # type: ignore
            placement=instance_data.get("placement/"), # type: ignore
            profile=instance_data.get("profile"), # type: ignore
            public_hostname=instance_data.get("public-hostname"), # type: ignore
            public_ipv4=instance_data.get("public-ipv4"), # type: ignore
            public_keys=instance_data.get("public-keys/"), # type: ignore
            region_name=instance_data.get("public-hostname").split(".")[1], # type: ignore
            reservation_id=instance_data.get("reservation-id"), # type: ignore
            security_groups=instance_data.get("security-groups"), # type: ignore
            services=instance_data.get("services/"), # type: ignore
            system=instance_data.get("system"), # type: ignore
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
        public_hostname = instance_data.get("public-hostname")
        instance_metadata.region_name = public_hostname.split(".")[1] if public_hostname and "." in public_hostname else None
        instance_metadata.reservation_id = instance_data.get("reservation-id")
        instance_metadata.security_groups = instance_data.get("security-groups")
        instance_metadata.services = instance_data.get("services/")
        instance_metadata.system = instance_data.get("system")
        instance_metadata.save()

    return jsonify(instance_data)