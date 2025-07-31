# cython: language_level=3
from src.models import InstanceMetadata
from src.helper.ec2_metadata import get_instance_metadata
from src.helper.logger import get_logger

logger = get_logger(__name__)

class Ec2MetadataService:
    @staticmethod
    def handle_instance_metadata() -> dict:
        data = get_instance_metadata()
        metadata = InstanceMetadata.query.first()

        if not metadata:
            logger.info("Instance metadata not found. Creating new instance metadata.")
            metadata = Ec2MetadataService._create_metadata(data)
        else:
            logger.info("Instance metadata found. Updating instance metadata.")
            metadata = Ec2MetadataService._update_metadata(metadata, data)

        metadata.save()
        return data

    @staticmethod
    def _create_metadata(data: dict) -> InstanceMetadata:
        return InstanceMetadata(
            ami_id=data.get("ami-id"), # type: ignore
            ami_launch_index=data.get("ami-launch-index"), # type: ignore
            ami_manifest_path=data.get("ami-manifest-path"), # type: ignore
            block_device_mapping=data.get("block-device-mapping/"), # type: ignore
            events=data.get("events/"), # type: ignore
            hostname=data.get("hostname"), # type: ignore
            identity_credentials=data.get("identity-credentials/"), # type: ignore
            instance_action=data.get("instance-action"), # type: ignore
            instance_id=data.get("instance-id"), # type: ignore
            instance_life_cycle=data.get("instance-life-cycle"), # type: ignore
            instance_type=data.get("instance-type"), # type: ignore
            local_hostname=data.get("local-hostname"), # type: ignore
            local_ipv4=data.get("local-ipv4"), # type: ignore
            mac=data.get("mac"), # type: ignore
            metrics=data.get("metrics/"), # type: ignore
            network=data.get("network/"), # type: ignore
            placement=data.get("placement/"), # type: ignore
            profile=data.get("profile"), # type: ignore
            public_hostname=data.get("public-hostname"), # type: ignore
            public_ipv4=data.get("public-ipv4"), # type: ignore
            public_keys=data.get("public-keys/"), # type: ignore
            region_name=data.get("public-hostname").split(".")[1] if data.get("public-hostname") and "." in data.get("public-hostname") else None, # type: ignore
            reservation_id=data.get("reservation-id"), # type: ignore
            security_groups=data.get("security-groups"), # type: ignore
            services=data.get("services/"), # type: ignore
            system=data.get("system") # type: ignore
        )

    @staticmethod
    def _update_metadata(metadata: InstanceMetadata, data: dict) -> InstanceMetadata:
        metadata.ami_id = data.get("ami-id")
        metadata.ami_launch_index = data.get("ami-launch-index")
        metadata.ami_manifest_path = data.get("ami-manifest-path")
        metadata.block_device_mapping = data.get("block-device-mapping/")
        metadata.events = data.get("events/")
        metadata.hostname = data.get("hostname")
        metadata.identity_credentials = data.get("identity-credentials/")
        metadata.instance_action = data.get("instance-action")
        metadata.instance_id = data.get("instance-id")
        metadata.instance_life_cycle = data.get("instance-life-cycle")
        metadata.instance_type = data.get("instance-type")
        metadata.local_hostname = data.get("local-hostname")
        metadata.local_ipv4 = data.get("local-ipv4")
        metadata.mac = data.get("mac")
        metadata.metrics = data.get("metrics/")
        metadata.network = data.get("network/")
        metadata.placement = data.get("placement/")
        metadata.profile = data.get("profile")
        metadata.public_hostname = data.get("public-hostname")
        metadata.public_ipv4 = data.get("public-ipv4")
        metadata.public_keys = data.get("public-keys/")
        metadata.region_name = data.get("public-hostname").split(".")[1] if data.get("public-hostname") and "." in data.get("public-hostname") else None # type: ignore
        metadata.reservation_id = data.get("reservation-id")
        metadata.security_groups = data.get("security-groups")
        metadata.services = data.get("services/")
        metadata.system = data.get("system")
        return metadata
