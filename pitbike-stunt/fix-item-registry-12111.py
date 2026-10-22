#!/usr/bin/env python3
"""Minecraft 1.21.11 Item.Settings must have a RegistryKey before constructing a custom item.
Fixes java.lang.NullPointerException: Item id not set on PitbikeStunt.onInitialize.
"""
from pathlib import Path

path=Path("project/src/main/java/dev/pitbike/stunt/PitbikeStunt.java")
src=path.read_text(encoding="utf-8")

before="""            BIKES[index] = Registry.register(Registries.ITEM,
                    id(v.name().toLowerCase()), new BikeItem(new Item.Settings().maxCount(1), index));"""
after="""            Identifier bikeId = id(v.name().toLowerCase(java.util.Locale.ROOT));
            RegistryKey<Item> bikeKey = RegistryKey.of(RegistryKeys.ITEM, bikeId);
            // Since Minecraft 1.21.2+, Item.Settings must know its RegistryKey
            // BEFORE the Item constructor executes, not after registry registration.
            BIKES[index] = Registry.register(Registries.ITEM,
                    bikeId, new BikeItem(new Item.Settings().registryKey(bikeKey).maxCount(1), index));"""
assert src.count(before) == 1, "Missing original registration; inspect new source before patching"
assert "import net.minecraft.registry.RegistryKey;" in src
assert "import net.minecraft.registry.RegistryKeys;" in src
src=src.replace(before,after)
assert ".registryKey(bikeKey)" in src
path.write_text(src,encoding="utf-8")
print("Fixed Pitbike Stunt startup crash: item IDs assigned before creation for all 6 bikes")
