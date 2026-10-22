#!/usr/bin/env python3
"""Upgrade the previously published 1.21.1 source ZIP to the 1.21.11 project.
The patched source is assembled on the CI runner for reproducibility.
"""
from pathlib import Path
import json

root = Path("project")
props = root / "gradle.properties"
s = props.read_text()
replacements = {
    "minecraft_version=1.21.1": "minecraft_version=1.21.11",
    "yarn_mappings=1.21.1+build.3": "yarn_mappings=1.21.11+build.6",
    "loader_version=0.16.14": "loader_version=0.19.5",
    "fabric_version=0.116.9+1.21.1": "fabric_version=0.141.6+1.21.11",
    "mod_version=0.2.0-alpha": "mod_version=0.3.0-alpha",
    "archives_base_name=pitbike-stunt-1.21.1": "archives_base_name=pitbike-stunt-1.21.11",
}
for a,b in replacements.items():
    assert a in s,a
    s=s.replace(a,b)
props.write_text(s)
p=root/"build.gradle"
s=p.read_text().replace("id 'fabric-loom' version '1.9.2'", "id 'fabric-loom' version '1.14.10'")
p.write_text(s)
p=root/"src/main/resources/fabric.mod.json"
data=json.loads(p.read_text())
data["depends"]["minecraft"]="=1.21.11"
data["depends"]["fabricloader"]=">=0.18.1"
p.write_text(json.dumps(data, indent=2,ensure_ascii=False)+"\n")
print("Upgraded to Minecraft 1.21.11, Loom 1.14, Yarn build.6 and Fabric API 0.141.6")
