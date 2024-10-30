from src.models.base_model import BaseModel
from src.config import db

class InstanceMetadata(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    ami_id = db.Column(db.String(50))
    ami_launch_index = db.Column(db.String(50))
    ami_manifest_path = db.Column(db.String(100))
    block_device_mapping = db.Column(db.Text)
    events = db.Column(db.String(50))
    hostname = db.Column(db.String(100))
    identity_credentials = db.Column(db.String(50))
    instance_action = db.Column(db.String(50))
    instance_id = db.Column(db.String(50))
    instance_life_cycle = db.Column(db.String(50))
    instance_type = db.Column(db.String(50))
    local_hostname = db.Column(db.String(100))
    local_ipv4 = db.Column(db.String(50))
    mac = db.Column(db.String(50))
    metrics = db.Column(db.String(50))
    network = db.Column(db.Text)
    placement = db.Column(db.Text)
    profile = db.Column(db.String(50))
    public_hostname = db.Column(db.String(100))
    public_ipv4 = db.Column(db.String(50))
    public_keys = db.Column(db.String(100))
    region_name = db.Column(db.String(50))
    reservation_id = db.Column(db.String(50))
    security_groups = db.Column(db.String(100))
    services = db.Column(db.Text)
    system = db.Column(db.String(50))

    def __repr__(self):
        return f'<InstanceMetadata instance_id={self.instance_id}>'
    
    def to_dict(self):
        if not self:
            return {}
        return {
            "ami_id": self.ami_id,
            "ami_launch_index": self.ami_launch_index,
            "ami_manifest_path": self.ami_manifest_path,
            "block_device_mapping": self.block_device_mapping,
            "events": self.events,
            "hostname": self.hostname,
            "identity_credentials": self.identity_credentials,
            "instance_action": self.instance_action,
            "instance_id": self.instance_id,
            "instance_life_cycle": self.instance_life_cycle,
            "instance_type": self.instance_type,
            "local_hostname": self.local_hostname,
            "local_ipv4": self.local_ipv4,
            "mac": self.mac,
            "metrics": self.metrics,
            "network": self.network,
            "placement": self.placement,
            "profile": self.profile,
            "public_hostname": self.public_hostname,
            "public_ipv4": self.public_ipv4,
            "public_keys": self.public_keys,
            "region_name": self.region_name,
            "reservation_id": self.reservation_id,
            "security_groups": self.security_groups,
            "services": self.services,
            "system": self.system
        }