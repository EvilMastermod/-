package com.rnmd.shadownpc;

import com.rnmd.shadownpc.item.NpcEditorItem;
import com.rnmd.shadownpc.network.OpenNpcEditorPayload;
import com.rnmd.shadownpc.network.SaveNpcPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.function.Function;

public final class ShadowNpcMod implements ModInitializer {
    public static final String MOD_ID = "shadow_npc";

    public static final Item NPC_STAFF = registerItem(
            "npc_staff",
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

    public static OpenNpcEditorPayload editorPayload(Villager npc) {
        return new OpenNpcEditorPayload(
                npc.getId(),
                npc.getName().getString(),
                NpcData.getDialog(npc),
                npc.isCustomNameVisible(),
                npc.isInvulnerable(),
                npc.isCurrentlyGlowing(),
                npc.isBaby(),
                NpcData.shouldLookAtPlayer(npc)
        );
    }

    @Override
    public void onInitialize() {
        PayloadTypeRegistry.clientboundPlay().register(OpenNpcEditorPayload.TYPE, OpenNpcEditorPayload.CODEC);
        PayloadTypeRegistry.serverboundPlay().register(SaveNpcPayload.TYPE, SaveNpcPayload.CODEC);

        ServerPlayNetworking.registerGlobalReceiver(SaveNpcPayload.TYPE, (payload, context) -> {
            ServerPlayer player = context.player();
            Entity entity = player.serverLevel().getEntity(payload.entityId());

            if (!(entity instanceof Villager npc) || !NpcData.isNpc(npc)) return;
            if (npc.distanceToSqr(player) > 64.0 * 64.0) return;

            if (payload.delete()) {
                npc.discard();
                player.displayClientMessage(Component.literal("§cNPC удалён."), false);
                return;
            }

            String name = payload.name() == null ? "" : payload.name().strip();
            if (name.isEmpty()) name = "NPC";
            if (name.length() > 48) name = name.substring(0, 48);

            npc.setCustomName(Component.literal(name));
            npc.setCustomNameVisible(payload.showName());
            npc.setInvulnerable(payload.invulnerable());
            npc.setGlowingTag(payload.glowing());
            npc.setBaby(payload.baby());
            npc.setNoAi(true);
            npc.setPersistenceRequired();

            NpcData.setDialog(npc, payload.dialog());
            NpcData.setLookAtPlayer(npc, payload.lookAtPlayer());

            player.displayClientMessage(Component.literal("§aNPC сохранён."), false);
        });

        ItemGroupEvents.modifyEntriesEvent(CreativeModeTabs.TOOLS_AND_UTILITIES)
                .register(entries -> entries.accept(NPC_STAFF));

        UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {
            if (!(entity instanceof Villager npc) || !NpcData.isNpc(npc)) {
                return InteractionResult.PASS;
            }

            ItemStack held = player.getItemInHand(hand);

            if (held.is(NPC_STAFF)) {
                if (!level.isClientSide() && player instanceof ServerPlayer serverPlayer) {
                    ServerPlayNetworking.send(serverPlayer, editorPayload(npc));
                }
                return InteractionResult.SUCCESS;
            }

            if (level.isClientSide()) return InteractionResult.SUCCESS;

            if (NpcData.shouldLookAtPlayer(npc)) {
                facePlayer(npc, player);
            }

            player.displayClientMessage(
                    Component.literal("§e" + npc.getName().getString() + ": §f" + NpcData.getDialog(npc)),
                    false
            );
            return InteractionResult.SUCCESS;
        });

        ServerTickEvents.END_LEVEL_TICK.register(level -> {
            for (Entity entity : level.getAllEntities()) {
                if (!(entity instanceof Villager npc) || !NpcData.isNpc(npc) || !NpcData.shouldLookAtPlayer(npc)) {
                    continue;
                }

                ServerPlayer nearest = null;
                double best = 12.0 * 12.0;
                for (ServerPlayer player : level.players()) {
                    if (player.isSpectator()) continue;
                    double dist = npc.distanceToSqr(player);
                    if (dist < best) {
                        best = dist;
                        nearest = player;
                    }
                }
                if (nearest != null) facePlayer(npc, nearest);
            }
        });
    }

    private static void facePlayer(Villager npc, Entity target) {
        double dx = target.getX() - npc.getX();
        double dz = target.getZ() - npc.getZ();
        float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        npc.setYRot(yaw);
        npc.setYHeadRot(yaw);
        npc.setYBodyRot(yaw);
    }
}
