package com.rnmd.shadownpc.item;

import com.rnmd.shadownpc.NpcData;
import com.rnmd.shadownpc.ShadowNpcMod;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

public final class NpcEditorItem extends Item {
    public NpcEditorItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }

        BlockPos spawnPos = context.getClickedPos().relative(context.getClickedFace());
        Villager npc = new Villager(EntityType.VILLAGER, level);
        npc.setPos(spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5);
        npc.setNoAi(true);
        npc.setPersistenceRequired();
        npc.setInvulnerable(true);
        npc.setCustomName(Component.literal("NPC"));
        npc.setCustomNameVisible(true);

        NpcData.markNpc(npc);
        NpcData.setDialog(npc, NpcData.DEFAULT_DIALOG);
        NpcData.setAnswer(npc, NpcData.DEFAULT_ANSWER);
        NpcData.setSkin(npc, NpcData.DEFAULT_SKIN);
        NpcData.setLookAtPlayer(npc, true);

        if (!level.addFreshEntity(npc)) {
            return InteractionResult.FAIL;
        }

        if (context.getPlayer() instanceof ServerPlayer player) {
            ServerPlayNetworking.send(player, ShadowNpcMod.editorPayload(npc));
        }

        return InteractionResult.SUCCESS;
    }
}
