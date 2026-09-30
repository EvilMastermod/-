package com.rnmd.shadownpc;

import com.rnmd.shadownpc.item.NpcEditorItem;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.function.Function;

public final class ShadowNpcMod implements ModInitializer {
    public static final String MOD_ID = "shadow_npc";

    public static final Item NPC_EDITOR = registerItem(
            "npc_editor",
            NpcEditorItem::new,
            new Item.Properties().stacksTo(1)
    );

    private static <T extends Item> T registerItem(String name, Function<Item.Properties, T> factory, Item.Properties properties) {
        Identifier id = Identifier.fromNamespaceAndPath(MOD_ID, name);
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, id);
        T item = factory.apply(properties.setId(key));
        Registry.register(BuiltInRegistries.ITEM, key, item);
        return item;
    }

    @Override
    public void onInitialize() {
        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.TOOLS_AND_UTILITIES)
                .register(entries -> entries.accept(NPC_EDITOR));

        UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {
            if (!(entity instanceof Villager npc) || !NpcData.isNpc(npc)) {
                return InteractionResult.PASS;
            }

            ItemStack held = player.getItemInHand(hand);

            if (held.is(Items.NAME_TAG)) {
                return InteractionResult.PASS;
            }

            if (level.isClientSide()) {
                return InteractionResult.PASS;
            }

            if (held.is(NPC_EDITOR)) {
                if (player.isShiftKeyDown()) {
                    npc.discard();
                    player.displayClientMessage(Component.literal("§cNPC удалён."), false);
                } else {
                    Component customName = held.get(DataComponents.CUSTOM_NAME);
                    if (customName != null) {
                        NpcData.setDialog(npc, customName.getString());
                        player.displayClientMessage(
                                Component.literal("§aДиалог NPC сохранён: §f" + NpcData.getDialog(npc)),
                                false
                        );
                    } else {
                        player.displayClientMessage(
                                Component.literal("§eПереименуй Редактор NPC в наковальне в нужную реплику и нажми им по NPC. §7Shift+ПКМ — удалить."),
                                false
                        );
                    }
                }
                return InteractionResult.SUCCESS;
            }

            player.displayClientMessage(
                    Component.literal("§e" + npc.getName().getString() + ": §f" + NpcData.getDialog(npc)),
                    false
            );
            return InteractionResult.SUCCESS;
        });
    }
}
